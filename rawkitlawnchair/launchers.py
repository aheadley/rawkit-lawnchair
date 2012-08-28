import usb.core
import functools

class AmmoEmptyError(Exception): pass

class BasicLauncher(object):
    LAUNCHER_DIDS   = []
    CAMERA_DIDS     = []
    _index = None
    _launcher = None
    _camera = None
    _ammo = 0

    @classmethod
    def watch_ammo(cls, wrapped):
        @functools.wraps(wrapped)
        def wrapper(self, *pargs, **kwargs):
            if not self.get_ammo_count():
                raise AmmoEmptyError()
            else:
                result = wrapped(self, *pargs, **kwargs)
                self._ammo -= 1
                return result
        return wrapper

    @classmethod
    def find_launchers(cls):
        return [dev for (v,p) in cls.LAUNCHER_DIDS \
            for dev in usb.core.find(idVendor=v, idProduct=p) \
            if dev is not None]

    def __init__(self, index=0, ammo_count=None):
        self._index = index
        self.reload(ammo_count)
        try:
            self._launcher = self.find_launchers()[self._index]
        except IndexError as err:
            raise ValueError('No launcher found for index: {0}'.format(self._index))
        if not hasattr(self._launcher, 'is_kernel_driver_active'):
            self._launcher = self._launcher.device
        if self._launcher.is_kernel_driver_active(0):
            self._launcher.detach_kernel_driver(0)
        self._launcher.set_configuration()

    def get_ammo_count(self):
        return self._ammo

    def get_launcher_device(self):
        return self._launcher

    def stop(self):
        raise NotImplemented()

    def reload(self, count=None):
        if count is None:
            count = self.AMMO_COUNT
        elif count < 0:
            count = 0
        self._ammo = min(self._ammo + count, self.AMMO_COUNT)

    move_up = move_down = move_left = move_right = fire = stop

class CameraLauncher(BasicLauncher):
    @classmethod
    def find_cameras(cls):
        return [cam for (v,p) in cls.CAMERA_DIDS \
            for cam in usb.core.find(idVendor=v, idProduct=p) \
            if cam is not None]

    def __init__(self, *args, **kwargs):
        super(CameraLauncher, self).__init__(*args, **kwargs)
        try:
            self._camera = self.find_cameras()[self._index]
        except IndexError as err:
            raise ValueError('No launcher-camera found for index: {0}'.format(self._index))

    def get_camera_device(self):
        return self._camera

class DreamCheeky_StormOIC(CameraLauncher):
    NAME            = 'Dream Cheeky - Storm O.I.C.'
    LAUNCHER_DIDS   = [(0x2123, 0x1010)]
    CAMERA_DIDS     = [(0x0c45, 0x6310)]
    AMMO_COUNT      = 4

    def stop(self):
        self._ctrl_launcher(0x02, 0x20)

    def move_up(self):
        self._ctrl_launcher(0x02, 0x02)

    def move_down(self):
        self._ctrl_launcher(0x02, 0x01)

    def move_left(self):
        self._ctrl_launcher(0x02, 0x04)

    def move_right(self):
        self._ctrl_launcher(0x02, 0x08)

    @CameraLauncher.watch_ammo
    def fire(self):
        self._ctrl_launcher(0x02, 0x10)

    def _ctrl_launcher(self, byte1, byte2):
        self._launcher.ctrl_transfer(0x21, 0x09, 0, 0,
            [byte1, byte2, 0, 0, 0, 0, 0, 0])

def marks_and_spencer_action(func):
    @functools.wraps(func)
    def wrapped(self):
        self._ctrl_launcher(self.CODE_INIT_A)
        self._ctrl_launcher(self.CODE_INIT_B)
        return func()
    return wrapped

class MarksAndSpencer_Launcher(BasicLauncher):
    NAME            = 'Marks & Spencer - Launcher'
    LAUNCHER_DIDS   = [(0x1130, 0x0202)]
    AMMO_COUNT      = 3

    CODE_STOP       = [0, 0, 0, 0, 0, 0, 8, 8]
    CODE_LEFT       = [0, 1, 0, 0, 0, 0, 8, 8]
    CODE_RIGHT      = [0, 0, 1, 0, 0, 0, 8, 8]
    CODE_UP         = [0, 0, 0, 1, 0, 0, 8, 8]
    CODE_DOWN       = [0, 0, 0, 0, 1, 0, 8, 8]
    CODE_FIRE       = [0, 0, 0, 0, 0, 1, 8, 8]
    CODE_INIT_A     = [85, 83, 66, 67, 0, 0, 4, 0]
    CODE_INIT_B     = [85, 83, 66, 67, 0, 64, 2, 0]

    @marks_and_spencer_action
    def stop(self):
        self._ctrl_launcher(self.CODE_STOP)

    @marks_and_spencer_action
    def move_up(self):
        self._ctrl_launcher(self.CODE_UP)

    @marks_and_spencer_action
    def move_down(self):
        self._ctrl_launcher(self.CODE_DOWN)

    @marks_and_spencer_action
    def move_left(self):
        self._ctrl_launcher(self.CODE_LEFT)

    @marks_and_spencer_action
    def move_right(self):
        self._ctrl_launcher(self.CODE_RIGHT)

    @BasicLauncher.watch_ammo
    @marks_and_spencer_action
    def fire(self):
        self._ctrl_launcher(self.CODE_FIRE)

    def _ctrl_launcher(self, ctrl_code):
        self._launcher.ctrl_transfer(0x21, 0x09, 0x02, 0x01, ctrl_code)
