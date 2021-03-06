
from .. import get_config
from ..util import PrototypeMixin, ContextAttribute
from .events import ContextChange
from . import wrappers

class Patch(PrototypeMixin):
    '''
    All patches are instances of this class.

    `parent` is the object being patched.
    `.on()` sets the replacement callable instead of the original one,
    `.off()` restores the initial state.

    Delegates the creation of the replacement callable to the
    wrapper class, which can be customized by passing `wrapper_type`.
    '''

    parent = None

    wrapper_type = ContextAttribute('wrapper_type', wrappers.Replacement)

    def __init__(self, attribute, parent=None,
                 prototype=None, **kwargs):
        PrototypeMixin.__init__(self, prototype, **kwargs)
        if parent:
            self.parent = parent
        assert self.parent is not None, "parent can't be None"
        self.attribute = attribute
        self.original = getattr(self.parent, self.attribute, None)
        self.wrapper = self.wrapper_type(prototype=self)(self.original)

    def on(self):
        setattr(self.parent, self.attribute, self.wrapper)

    def off(self):
        if self.original:
            setattr(self.parent, self.attribute, self.original)
        else:
            delattr(self.parent, self.attribute)

    @property
    def is_on(self):
        return getattr(self.parent, self.attribute) != self.original

    def __repr__(self):
        # TODO
        try:
            return "Patch %s.%s" % (self.parent.__name__, self.original.__name__)
        except:
            return super().__repr__()

# ugly, just a proof of concept
class SimpleConditionalPatch(Patch):
    '''
    Patch that gets enabled (and applied) on a certain event.
    '''

    listen_to = ContextAttribute('listen_to', ContextChange)

    def __init__(self, *args, **kw):
        super(SimpleConditionalPatch, self).__init__(*args, **kw)
        self._enabled = False
        get_config().register_event_handler(self.listen_to, self.enable)

    def on(self):
        if not self._enabled:
            return
        super(SimpleConditionalPatch, self).on()

    def enable(self, *args, **kw):
        Patch.on(self)
        self._enabled = True
        get_config().unregister_event_handler(self.listen_to, self.enable)
