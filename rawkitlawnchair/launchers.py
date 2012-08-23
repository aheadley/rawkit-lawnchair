import usb.core
import functools

class AmmoEmptyError(Exception): pass

class BaseLauncher(object):
    LAUNCHER_DIDS   = []
    CAMERA_DIDS     = []
    _index = None
    _launcher = None
    _camera = None
    _ammo = 0

    @staticmethod
    def watch_ammo(wrapped):
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

    @classmethod
    def find_cameras(cls):
        if cls.CAMERA_DIDS:
            return [cam for (v,p) in cls.CAMERA_DIDS \
                for cam in usb.core.find(idVendor=v, idProduct=p) \
                if cam is not None]
        else:
            return []

    def __index__(self, index=0, ammo_count=None):
        self._index = index
        self.reload(ammo_count)
        try:
            self._launcher = self.find_launchers()[self._index]
        except IndexError as err:
            raise ValueError('No launcher found for index: {0}'.format(self._index))
        if self._launcher.is_kernel_driver_active(0):
            self._launcher.detach_kernel_driver(0)
        self._launcher.set_configuration()

        if self.CAMERA_DIDS:
            try:
                self._camera = self.find_cameras()[self._index]
            except IndexError as err:
                raise ValueError('No launcher-camera found for index: {0}'.format(self._index))

    def get_ammo_count(self):
        return self._ammo

    def get_launcher_device(self):
        return self._launcher

    def get_camera_device(self):
        return self._camera

    def stop(self):
        raise NotImplemented()

    def reload(count=None):
        if count is None:
            count = self.AMMO_COUNT
        elif count < 0:
            count = 0
        self._ammo = min(self._ammo + count, self.AMMO_COUNT)

    move_up = move_down = move_left = move_right = fire = stop

class DreamCheeky_StormOIC(BaseLauncher):
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

    @BaseLauncher.watch_ammo
    def fire(self):
        self._ctrl_launcher(0x02, 0x10)

    def _ctrl_launcher(self, byte1, byte2):
        self._launcher.ctrl_transfer(0x21, 0x09, 0, 0,
            [byte1, byte2, 0, 0, 0, 0, 0, 0])
