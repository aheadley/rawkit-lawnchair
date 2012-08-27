import SimpleCV
import numpy
import time

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @property
    def area(self):
        return self.x * self.y

class BaseKernel(object):
    CONFIG = {
        'debug': True,
    }

    def __init__(self, launcher, **kwargs):
        self._launcher = launcher
        self._config = self.CONFIG.copy()
        self._config.update(kwargs)

    def run(self):
        raise NotImplemented()

class CameraKernel(BaseKernel):
    def __init__(self, *pargs, **kwargs):
        super(CameraKernel, self).__init__(*pargs, **kwargs)
        #self._camera = SimpleCV.Camera(index=self._get_camera_index())
        self._camera = SimpleCV.Camera(1)
        self._camera_props = self._camera.getAllProperties()

    def _get_camera_index(self):
        return self._launcher._index

class PanTracker(CameraKernel):
    _last_img = None

    def run(self):
        if self._config['debug']:
            disp = SimpleCV.Display()
        self._last_img = self._get_new_image()
        img_size = Point(*self._last_img.size())
        img_center = Point(img_size.x/2, img_size.y/2)
        max_blob_size = img_size.area * 0.40
        min_blob_size = img_size.area * 0.02
        diff_threshold = 0.10
        size_threshold = 0.60
        target_blob = None
        self._base_sleep_time = 0.20
        while disp.isNotDone() if self._config['debug'] else True:
            self._launcher.stop()
            time.sleep(self._base_sleep_time)
            new_img = self._get_new_image(True)
            if self._config['debug']:
                new_img.save(disp)
            if target_blob is None:
                #no target, try to find one
                self._debug_msg('Scanning for new target between {0} and {1} pixels',
                    min_blob_size, max_blob_size)
                diff = new_img - self._last_img
                if self._config['debug']:
                    diff.show()
                diff_pixels = diff.getNumpy().flatten()
                diff_percent = float(numpy.count_nonzero(diff_pixels)) / float(len(diff_pixels))
                if diff_percent > diff_threshold:
                    self._debug_msg('Movement detected: {0}', diff_percent)
                    new_target_blob = self._acquire_target(None, min_blob_size, max_blob_size, diff)
                    if new_target_blob:
                        self._debug_msg('Target candidate found: {0}', new_target_blob)
                        new_target_blob = self._acquire_target(new_target_blob.meanColor(),
                            min_blob_size, max_blob_size, new_img)
                        if new_target_blob:
                            self._debug_msg('Target acquired')
                            target_blob = new_target_blob
                            target_blob.show(color=SimpleCV.Color.RED)
                            self._last_img = new_img
                            #let target handling aim at the target
                            #time.sleep(self._pick_move(img_center, Point(*target_blob.centroid())))
                        else:
                            self._debug_msg('Target candidate not usable')
                            #self._last_img = new_img
                            time.sleep(self._base_sleep_time * 0.50)
                    else:
                        #miss
                        self._debug_msg('No target candidates found')
                        #intentionally not changing _last_img
                        time.sleep(self._base_sleep_time * 0.50) #let it move some more
                else:
                    self._debug_msg('No movement detected')
                    self._last_img = new_img
                    time.sleep(self._base_sleep_time)
            else:
                #had a target, try to find it again
                self._debug_msg('Searching for previous target')
                target_min_size = target_blob.area() * (1.0 - size_threshold)
                target_max_size = target_blob.area() * (1.0 + size_threshold)
                prev_target_blob = self._acquire_target(target_blob.meanColor(),
                    target_min_size, target_max_size, new_img)
                if prev_target_blob:
                    self._debug_msg('Re-acquired previous target')
                    target_blob = prev_target_blob
                    self._last_img = new_img
                    time.sleep(self._pick_move(img_center, Point(*target_blob.centroid())))
                else:
                    self._debug_msg('Previous target not found')
                    target_blob = None
                    self._last_img = new_img
                    time.sleep(self._base_sleep_time)

    def _debug_msg(self, msg, *pargs, **kwargs):
        if self._config['debug']:
            print msg.format(*pargs, **kwargs)

    def _get_new_image(self, color=False):
        img = self._camera.getImage()
        if not color:
            img = img.greyscale()
        return img

    def _pick_move(self, img_center, blob_center):
        x = img_center.x - blob_center.x
        y = img_center.y - blob_center.y
        if abs(x) > abs(y):
            if abs(x) > 30:
                if x > 0:
                    self._launcher.move_left()
                else:
                    self._launcher.move_right()
                return (abs(float(x)) / self._camera_props['width']) * self._base_sleep_time
            else:
                return self._base_sleep_time
        else:
            if abs(y) > 15:
                if y > 0:
                    self._launcher.move_up()
                else:
                    self._launcher.move_down()
                return (abs(float(y)) / self._camera_props['height']) * self._base_sleep_time
            else:
                return self._base_sleep_time

    def _acquire_target(self, target_color, min_size, max_size, image):
        blobs = image.findBlobs(minsize=min_size, maxsize=max_size)
        if blobs:
            if self._config['debug']:
                blobs.show(color=SimpleCV.Color.BLUE)
            if target_color:
                return blobs.sortColorDistance(color=target_color)[0]
            else:
                return blobs.sortArea()[0]
        else:
            return None

