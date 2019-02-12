import traceback

import petram.debug
dprint1, dprint2, dprint3 = petram.debug.init_dprints('PP_Mode')

from petram.helper.variables import var_g
ll = var_g.copy()

from petram.model import Model
class PostProcessBase(Model):
    def run_postprocess(self, engin):
        raise NotImplemented("Subclass must implement run_postprocess")
    
    def onItemSelChanged(self, evt):
        '''
        GUI response when model object is selected in
        the dlg_edit_model
        '''
        viewer = evt.GetEventObject().GetTopLevelParent().GetParent()
        viewer.set_view_mode('phys')
        
    def soldict_to_solvars(self, soldict, variables):
        pass
    
class PostProcess(PostProcessBase):
    def get_possible_child(self):
        from petram.postprocess.project_solution import DerivedValue
        from petram.postprocess.discrt_v_integration import DiscrtVIntegration        
        return [DerivedValue, DiscrtVIntegration]

    def run_postprocess(self, engine):
        dprint1("running postprocess:" + self.name())

    def run(self, engine):
        for mm in self.walk():
            if not mm.enabled: continue            
            mm.run_postprocess(engine)


