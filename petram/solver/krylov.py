'''

Krylov Model. 
  Krylov solver
  This model is supposeed to work inside Iteratife solver chain.
  This model itsel does not define an iterative solver itself.

'''
from petram.solver.mumps_model import MUMPSPreconditioner
from petram.mfem_config import use_parallel
import numpy as np

from petram.debug import flush_stdout
from petram.namespace_mixin import NS_mixin
from .solver_model import LinearSolverModel, LinearSolver

import petram.debug as debug
dprint1, dprint2, dprint3 = debug.init_dprints('KrylovModel')

if use_parallel:
    from petram.helper.mpi_recipes import *
    from mfem.common.parcsr_extra import *
    import mfem.par as mfem
    default_kind = 'hypre'

    from mpi4py import MPI
    num_proc = MPI.COMM_WORLD.size
    myid = MPI.COMM_WORLD.rank
    smyid = '{:0>6d}'.format(myid)
    from mfem.common.mpi_debug import nicePrint

else:
    import mfem.ser as mfem
    default_kind = 'scipy'

choices_a = ['CG', 'GMRES', 'FGMRES', 'BiCGSTAB', 'MINRES']

single1_elp = [["log_level", -1, 400, {}],
               ["max  iter.", 200, 400, {}],
               ["rel. tol", 1e-7, 300, {}],
               ["abs. tol.", 1e-7, 300, {}], ]
single2_elp = [["log_level", -1, 400, {}],
               ["max  iter.", 200, 400, {}],
               ["rel. tol", 1e-7, 300, {}],
               ["abs. tol.", 1e-7, 300, {}],
               ["restart(kdim)", 50, 400, {}]]


class KrylovModel(LinearSolverModel, NS_mixin):
    hide_ns_menu = True
    has_2nd_panel = False
    accept_complex = False
    always_new_panel = False

    def __init__(self, *args, **kwargs):
        LinearSolverModel.__init__(self, *args, **kwargs)
        NS_mixin.__init__(self, *args, **kwargs)

    def init_solver(self):
        pass

    def panel1_param(self):
        return [[None, None, 34, [{'text': "Solver", 'choices': choices_a},
                                  {'elp': single1_elp},  # CG
                                  {'elp': single2_elp},  # GMRES
                                  {'elp': single2_elp},  # FGMRES
                                  {'elp': single1_elp},  # BiCGSTAB
                                  {'elp': single1_elp},  # MINRES
                                  ], ],
                [None, self.write_mat, 3, {"text": "write matrix"}],
                [None, self.assert_no_convergence, 3,
                    {"text": "check converegence"}],]

    def get_panel1_value(self):
        # this will set _mat_weight
        from petram.solver.solver_model import SolveStep
        p = self.parent
        while not isinstance(p, SolveStep):
            p = p.parent
            if p is None:
                assert False, "Solver is not under SolveStep"

        single1 = [int(self.log_level), int(self.maxiter),
                   self.reltol, self.abstol]
        single2 = [int(self.log_level), int(self.maxiter),
                   self.reltol, self.abstol, int(self.kdim)]
        value = ([self.solver_type, single1, single2, single2,
                  single1, single1],
                 self.write_mat, self.assert_no_convergence,)

        return value

    def import_panel1_value(self, v):
        self.solver_type = str(v[0][0])
        idx = choices_a.index(self.solver_type)
        vv = v[0][idx + 1]
        self.log_level = int(vv[0])
        self.maxiter = int(vv[1])
        self.reltol = vv[2]
        self.abstol = vv[3]

        if len(vv) > 4:
            self.kdim = int(vv[4])

        self.write_mat = bool(v[1])
        self.assert_no_convergence = bool(v[2])

    def attribute_set(self, v):
        v = super(KrylovModel, self).attribute_set(v)
        v['solver_type'] = 'GMRES'
        v['log_level'] = 0
        v['maxiter'] = 200
        v['reltol'] = 1e-7
        v['abstol'] = 1e-7
        v['kdim'] = 50

        v['printit'] = 1
        v['write_mat'] = False
        v['assert_no_convergence'] = True
        return v

    def get_possible_child(self):
        from petram.solver.mumps_model import MUMPS
        from petram.solver.block_smoother import DiagonalPreconditioner
        
        return KrylovModel, MUMPS, DiagonalPreconditioner

    def get_possible_child_menu(self):
        from petram.solver.mumps_model import MUMPS
        from petram.solver.block_smoother import DiagonalPreconditioner
        
        choice = [("Preconditioner", KrylovSmoother),
                  ("", MUMPS),
                  ("!", DiagonalPreconditioner),]
        return choice
    
    def verify_setting(self):
        return True, "", ""

    def allocate_solver(self, is_complex=False, engine=None):
        raise NotImplementedError(
            "you must specify this method in subclass")
        
    def linear_system_type(self, assemble_real, phys_real):
        raise NotImplementedError(
            "you must specify this method in subclass")
        
    def real_to_complex(self, solall, M):
        if self.merge_real_imag:
            return self.real_to_complex_merged(solall, M)
        else:
            return self.real_to_complex_interleaved(solall, M)

    def real_to_complex_interleaved(self, solall, M):
        if use_parallel:
            from mpi4py import MPI
            myid = MPI.COMM_WORLD.rank

            offset = M.RowOffsets().ToList()
            of = [np.sum(MPI.COMM_WORLD.allgather(np.int32(o)))
                  for o in offset]
            if myid != 0:
                return

        else:
            offset = M.RowOffsets()
            of = offset.ToList()

        rows = M.NumRowBlocks()
        s = solall.shape
        nb = rows // 2
        i = 0
        pt = 0
        result = np.zeros((s[0] // 2, s[1]), dtype='complex')
        for j in range(nb):
            l = of[i + 1] - of[i]
            result[pt:pt + l, :] = (solall[of[i]:of[i + 1], :]
                                    + 1j * solall[of[i + 1]:of[i + 2], :])
            i = i + 2
            pt = pt + l

        return result

    def real_to_complex_merged(self, solall, M):
        if use_parallel:
            from mpi4py import MPI
            myid = MPI.COMM_WORLD.rank

            offset = M.RowOffsets().ToList()
            of = [np.sum(MPI.COMM_WORLD.allgather(np.int32(o)))
                  for o in offset]
            if myid != 0:
                return

        else:
            offset = M.RowOffsets()
            of = offset.ToList()
        dprint1(of)
        rows = M.NumRowBlocks()
        s = solall.shape
        i = 0
        pt = 0
        result = np.zeros((s[0] // 2, s[1]), dtype='complex')
        for i in range(rows):
            l = of[i + 1] - of[i]
            w = int(l // 2)
            result[pt:pt + w, :] = (solall[of[i]:of[i] + w, :]
                                    + 1j * solall[(of[i] + w):of[i + 1], :])
            pt = pt + w
        return result

    def allocate_solver(self, is_complex=False, engine=None):
        solver = IterativeSolver(self, engine, int(self.maxiter),
                                 self.abstol, self.reltol, int(self.kdim))
        # solver.AllocSolver(datatype)
        return solver

    def get_possible_child(self):
        '''
        Preconditioners....
        '''
        choice = []
        try:
            from petram.solver.mumps_model import MUMPS
            choice.append(MUMPS)
        except ImportError:
            pass
        return choice

    @classmethod
    def fancy_menu_name(self):
        return 'KrylovSolver'

    @classmethod
    def fancy_tree_name(self):
        return 'Krylov'

    def get_info_str(self):
        return 'Solver'

    def does_linearsolver_choose_linearsystem_type(self):
        return False

    def supported_linear_system_type(self):
        return ["blk_interleave",
                "blk_merged_s",
                "blk_merged",]

class KrylovSmoother(KrylovModel):
    @classmethod
    def fancy_menu_name(self):
        return 'KrylovSmoother'

    @classmethod
    def fancy_tree_name(self):
        return 'Krylov'

    def get_info_str(self):
        return 'Smoother'
    
    def get_possible_child(self):
        from petram.solver.mumps_model import MUMPS
        from petram.solver.block_smoother import DiagonalPreconditioner
        
        return KrylovModel, MUMPS, DiagonalPreconditioner

    def get_possible_child_menu(self):
        from petram.solver.mumps_model import MUMPS
        from petram.solver.block_smoother import DiagonalPreconditioner
        
        choice = [("Preconditioner", KrylovSmoother),
                  ("", MUMPS),
                  ("!", DiagonalPreconditioner),]
        return choice


class KrylovLinearSolver(LinearSolver):
    is_iterative = True

    def __init__(self, gui, engine):
        self.maxiter = gui.maxiter
        self.abstol = gui.abstol
        self.reltol = gui.reltol
        self.kdim = gui.kdim
        LinearSolver.__init__(self, gui, engine)

    def SetOperator(self, opr, dist=False, name=None):
        self.Aname = name
        self.A = opr

        from petram.solver.linearsystem_reducer import LinearSystemReducer
        if use_parallel:
             self.M = self.make_preconditioner(self.A, parallel=True)
             self.solver = self.make_solver(self.A, self.M, use_mpi=True)
        else:
            self.M = self.make_preconditioner(self.A)
            self.solver = self.make_solver(self.A, self.M)

    def Mult(self, b, x=None, case_base=0):
        if use_parallel:
            return self.solve_parallel(self.A, b, x)
        else:
            return self.solve_serial(self.A, b, x)

    def make_solver(self, A, M, use_mpi=False):
        maxiter = int(self.maxiter)
        atol = self.abstol
        rtol = self.reltol
        kdim = int(self.kdim)
        printit = 1

        args = (MPI.COMM_WORLD,) if use_mpi else ()

        if self.gui.solver_type.startswith("Nested"):
            solver_type = self.gui.solver_type.split(" ")[-1]
            nested = True
        else:
            solver_type = self.gui.solver_type
            nested = False
        cls = getattr(mfem, solver_type + 'Solver')

        solver = cls(*args)
        if solver_type in ['GMRES', 'FGMRES']:
            solver.SetKDim(kdim)

        if nested:
            inner_solver_type = self.gui.solver_type_in
            if inner_solver_type != "MUMPS":
                cls = getattr(mfem, inner_solver_type + 'Solver')
                inner_solver = cls(*args)
                inner_solver.SetAbsTol(0.0)
                inner_solver.SetRelTol(0.0)
                inner_solver.SetMaxIter(self.gui.maxiter_in)
                inner_solver.SetPrintLevel(self.gui.log_level_in)
                if inner_solver_type in ['GMRES', 'FGMRES']:
                    inner_solver.SetKDim(int(self.gui.kdim_in))
                inner_solver.iterative_mode = False
                inner_solver.SetOperator(A)
                inner_solver.SetPreconditioner(M)
                # return inner_solver
                prc = inner_solver
            else:
                from petram.solver.mumps_model import MUMPSBlockPreconditioner
                prc = MUMPSBlockPreconditioner(A, gui=self.gui[self.gui.mumps_in],
                                               engine=self.engine)

        else:
            prc = M
        solver._prc = prc
        solver.SetPreconditioner(prc)
        solver.SetOperator(A)

        solver.SetAbsTol(atol)
        solver.SetRelTol(rtol)
        solver.SetMaxIter(maxiter)
        solver.SetPrintLevel(self.gui.log_level)

        return solver

    def make_preconditioner(self, A, name=None, parallel=False):
        name = self.Aname if name is None else name

        if self.gui.adv_mode:
            expr = self.gui.adv_prc
            gen = eval(expr, self.gui._global_ns)
            gen.set_param(A, name, self.engine, self.gui)
            M = gen()

        else:
            prcs_gui = dict(self.gui.preconditioners)
            #assert not self.gui.parent.is_complex(), "can not solve complex"
            if self.gui.parent.is_converted_from_complex() and not self.gui.merge_real_imag:
                name = sum([[n, n] for n in name], [])

            import petram.helper.preconditioners as prcs

            g = prcs.DiagonalPrcGen(
                opr=A, engine=self.engine, gui=self.gui, name=name)
            M = g()

            pc_block = {}

            for k, n in enumerate(name):
                prctxt = prcs_gui[n][1] if parallel else prcs_gui[n][0]
                if prctxt == "None":
                    continue
                if prctxt.find("(") == -1:
                    prctxt = prctxt + "()"
                prcargs = "(".join(prctxt.split("(")[-1:])

                nn = prctxt.split("(")[0]

                if not n in pc_block:
                    # make a new one
                    dprint1(nn)
                    try:
                        blkgen = getattr(prcs, nn)
                    except BaseException:
                        if nn in self.gui._global_ns:
                            blkgen = self.gui._global_ns[nn]
                        else:
                            raise

                    blkgen.set_param(g, n)
                    blk = eval("blkgen(" + prcargs)

                    M.SetDiagonalBlock(k, blk)
                    pc_block[n] = blk
                else:
                    M.SetDiagonalBlock(k, pc_block[n])
        return M

    def write_mat(self, A, b, x, suffix=""):
        def get_block(Op, i, j):
            try:
                return Op._linked_op[(i, j)]
            except KeyError:
                return None

        offset = A.RowOffsets()
        rows = A.NumRowBlocks()
        cols = A.NumColBlocks()

        for i in range(cols):
            for j in range(rows):
                m = get_block(A, i, j)
                if m is None:
                    continue
                m.Print('matrix_' + str(i) + '_' + str(j))
        for i, bb in enumerate(b):
            for j in range(rows):
                v = bb.GetBlock(j)
                v.Print('rhs_' + str(i) + '_' + str(j) + suffix)
                #np.save('rhs_' + str(i) + '_' + str(j) + suffix, v.GetDataArray())
        if x is not None:
            for j in range(rows):
                xx = x.GetBlock(j)
                xx.Print('x_' + str(i) + '_' + str(j) + suffix)

    @flush_stdout
    def call_mult(self, solver, bb, xx):
        print(np.sum(bb.GetDataArray()), np.sum(xx.GetDataArray()))
        solver.Mult(bb, xx)
        max_iter = solver.GetNumIterations()
        tol = solver.GetFinalNorm()

        dprint1("convergence check (max_iter, tol) ", max_iter, " ", tol)
        if self.gui.assert_no_convergence:
            if not solver.GetConverged():
                self.gui.set_solve_error(
                    (True, "No Convergence: " + self.gui.name()))
                assert False, "No convergence"

    def solve_parallel(self, A, b, x=None):
        if self.gui.write_mat:
            self. write_mat(A, b, x, "." + smyid)

        sol = []

        # solve the problem and gather solution to head node...
        # may not be the best approach

        from petram.helper.mpi_recipes import gather_vector
        offset = A.RowOffsets()
        for bb in b:
            rows = MPI.COMM_WORLD.allgather(np.int32(bb.Size()))
            #rowstarts = np.hstack((0, np.cumsum(rows)))
            dprint1("row offset", offset.ToList())
            if x is None:
                xx = mfem.BlockVector(offset)
                xx.Assign(0.0)
            else:
                xx = x

            if self.gui.use_ls_reducer:
                try:
                    self.reducer.Mult(bb, xx, self.gui.assert_no_convergence)
                except debug.ConvergenceError:
                    self.gui.set_solve_error(
                        (True, "No Convergence: " + self.gui.name()))
                    assert False, "No convergence"
            else:
                self.call_mult(self.solver, bb, xx)

            s = []
            for i in range(offset.Size() - 1):
                v = xx.GetBlock(i).GetDataArray()
                if self.gui.merge_real_imag:
                    w = int(len(v) // 2)
                    vv1 = gather_vector(v[:w])
                    vv2 = gather_vector(v[w:])
                    vv = np.hstack((vv1, vv2))
                else:
                    vv = gather_vector(v)
                if myid == 0:
                    s.append(vv)
                else:
                    pass
            if myid == 0:
                sol.append(np.hstack(s))

        if myid == 0:
            sol = np.transpose(np.vstack(sol))
            return sol
        else:
            return None

    def solve_serial(self, A, b, x=None):
        if self.gui.write_mat:
            self. write_mat(A, b, x)

        #M = self.M
        solver = self.solver

        sol = []

        for bb in b:
            if x is None:
                xx = mfem.Vector(bb.Size())
                xx.Assign(0.0)
            else:
                xx = x
                # for j in range(cols):
                #   print x.GetBlock(j).Size()
                #   print x.GetBlock(j).GetDataArray()
                #assert False, "must implement this"
            self.call_mult(solver, bb, xx)

            sol.append(xx.GetDataArray().copy())
        sol = np.transpose(np.vstack(sol))
        return sol
    
