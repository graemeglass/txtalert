# Adapted from http://stackoverflow.com/questions/110803/dirty-fields-in-django
from django.db.models.signals import post_save

class DirtyFieldsMixin(object):
    def __init__(self, *args, **kwargs):
        super(DirtyFieldsMixin, self).__init__(*args, **kwargs)
        post_save.connect(self._reset_state, sender=self.__class__, 
                            dispatch_uid='%s-DirtyFieldsMixin-sweeper' % self.__class__.__name__)
        self._reset_state()
    
    def _reset_state(self, *args, **kwargs):
        self._original_state = self._as_dict()
    
    def _as_dict(self):
        return dict([(f.name, getattr(self, f.name)) for f in self._meta.local_fields if not f.rel])
    
    def get_dirty_fields(self):
        new_state = self._as_dict()
        return dict([(key, value) for key, value in self._original_state.iteritems() if value != new_state[key]])
    
