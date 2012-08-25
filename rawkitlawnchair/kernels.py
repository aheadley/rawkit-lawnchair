import SimpleCV
import numpy
import time

class BaseKernel(object):
    def __init__(self, launcher):
        self._launcher = launcher

    def run(self):
        raise NotImplemented()

class CameraKernel(BaseKernel):
    def __init__(self, *pargs, **kwargs):
        super(CameraKernel, self).__init__(*pargs, **kwargs)
        #self._camera = SimpleCV.Camera(index=self._get_camera_index())
        self._camera = SimpleCV.Camera(1)

    def _get_camera_index(self):
        return self._launcher._index

class PanTracker(CameraKernel):
    _last_img = None

    def run(self):
        disp = SimpleCV.Display()
        self._last_img = self._get_new_image()
        (x, y) = self._last_img.size()
        center = (x / 2, y / 2)
        while True:
            self._launcher.stop()
            new_img = self._get_new_image()
            new_img.save(disp)
            blobs = new_img.findBlobs(maxsize=center[0]*center[1]*1.5, minsize=center[1])
            if blobs:
                big_blob = blobs[-1]
                big_blob.show()
                blob_center = big_blob.centroid()
                x = center[0] - blob_center[0]
                y = center[1] - blob_center[1]
                self._pick_move(x, y)
            self._last_img = new_img
            time.sleep(0.2)

    def _get_new_image(self):
        return self._camera.getImage().greyscale()

    def _pick_move(self, x, y):
        if abs(x) > abs(y):
            if abs(x) > 10:
                if x > 0:
                    self._launcher.move_left()
                else:
                    self._launcher.move_right()
        else:
            if abs(y) > 20:
                if y > 0:
                    self._launcher.move_up()
                else:
                    self._launcher.move_down()
