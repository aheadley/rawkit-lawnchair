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
        self._camera_props = self._camera.getAllProperties()

    def _get_camera_index(self):
        return self._launcher._index

class PanTracker(CameraKernel):
    _last_img = None

    def run(self):
        disp = SimpleCV.Display()
        self._last_img = self._get_new_image()
        (x, y) = self._last_img.size()
        center = (x / 2, y / 2)
        mx = center[0] * center[1] * 1.5
        mn = center[0] * center[1] * 0.25
        changed_threshold = 0.05
        size_threshold = 0.30
        target = None
        while disp.isNotDone():
            self._launcher.stop()
            time.sleep(0.1)
            new_img = self._get_new_image()
            new_img.save(disp)
            if target:
                #had a target, try to find it again
                print 'searching for previous target'
                buf = size_threshold * target[1]
                blobs = new_img.findBlobs(minsize=mn)
                if blobs:
                    print 'previous target candidates found'
                    blobs = [blob for blob in blobs.sortColorDistance(color=target[0]) \
                        if blob.area() < (target[1] + buf) and blob.area() > (target[1] - buf)]
                if blobs:
                    print 'found previous target'
                    target_blob = blobs[0]
                    #target_blob = blobs.sortColorDistance(color=target[0])[0]
                    target = (target_blob.meanColor(), target_blob.area())
                    self._last_img = new_img
                    #time.sleep(self._pick_move(center, target_blob.centroid()))
                    t = self._pick_move(center, target_blob.centroid())
                    print 'sleeping for %f' % t
                    time.sleep(t)
                else:
                    #target lost
                    print 'target lost'
                    target = None
                    self._last_img = new_img
                    time.sleep(0.5)
            else:
                #no target, try to find one
                print 'scanning for new target'
                diff = new_img - self._last_img
                diff.show()
                diff_px = diff.getNumpy().flatten()
                if (float(numpy.count_nonzero(diff_px)) / float(len(diff_px))) > changed_threshold:
                    #new target
                    print 'new target candidates found'
                    blobs = diff.findBlobs(minsize=mn)
                    if blobs:
                        #hit
                        print 'new target acquired'
                        target_blob = blobs[-1]
                        target_blob.show(color=SimpleCV.Color.RED)
                        target = (target_blob.meanColor(), target_blob.area())
                        self._last_img = new_img
                        #time.sleep(self._pick_move(center, target_blob.centroid()))
                        t = self._pick_move(center, target_blob.centroid())
                        print 'sleeping for %f' % t
                        time.sleep(t)
                    else:
                        #miss
                        print 'no viable targets'
                        #intentionally not changing _last_img
                        time.sleep(0.05) #let it move some more
                else:
                    #all clear on the western front
                    print 'no targets found'
                    self._last_img = new_img
                    time.sleep(0.5)

    def _get_new_image(self, color=False):
        img = self._camera.getImage()
        if not color:
            img = img.greyscale()
        return img

    def _pick_move(self, img_center, blob_center):
        x = img_center[0] - blob_center[0]
        y = img_center[1] - blob_center[1]
        if abs(x) > abs(y):
            if abs(x) > 30:
                if x > 0:
                    self._launcher.move_left()
                else:
                    self._launcher.move_right()
                return (abs(float(x)) / self._camera_props['width']) * 0.2
            else:
                return 0.1
        else:
            if abs(y) > 15:
                if y > 0:
                    self._launcher.move_up()
                else:
                    self._launcher.move_down()
                return (abs(float(y)) / self._camera_props['height']) * 0.3
            else:
                return 0.1

