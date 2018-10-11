from os import path
from scipy import misc

class SnipBBOX(object):

    def __init__(self):
        self.bbox = None
        self.imgpath = None
        self.img = None
        self.ftype = None
        self.opath = None
        self.imgarr = None
        self.imgsnippet = None

    def load_image(self, imgpath):
        try:
            self.imgpath = imgpath
            self.img = path.basename(imgpath)
            self.ftype = self.img.split(".")[-1]
            if self.ftype.lower() not in ["jpg", "png", "bmp", "gif", "tiff"]:
                raise NameError
            self.imgarr = misc.imread(f"{self.imgpath}")
            self.imgsnippet = self.imgarr
            self.bbox = self.imgarr.shape
        except IOError:
            print(f"cannot open {self.imgpath}")
        except NameError:
            print(f"The image filetype {self.ftype} is not supported!")
        return None

    def store_image(self, opath):
        try:
            if self.img is None:
                raise NameError
            bboxstr = "_".join(str(bboxval) for bboxval in self.bbox)
            self.opath = opath + self.img.split(".")[0] + "bbox_" + bboxstr +  "." + ".".join(self.img.split(".")[1:])
            misc.imsave(self.opath, self.imgsnippet)
        except NameError:
            print("Please load an image first.")
        except:
            print(f"{self.ospath} could not be stored.")
        return

    def set_bbox(self, bbox):
        try:
            if self.imgarr is None:
                raise NameError
            if bbox[:1] < [0,0] and bbox[2:3] < self.imgarr.shape[:1]:
                raise ValueError
            if not isinstance(bbox,list) or len(bbox) != 4:
                raise TypeError
            if bbox != self.bbox:
                self.bbox = bbox
                self.imgsnippet = self.imgarr[bbox[0]:bbox[2],bbox[1]:bbox[3],:self.imgarr.shape[2]]
        except TypeError:
            print("The bbox has not the right type or format.")
        except NameError:
            print("Please load an image first.")
        except ValueError:
            print("The bbox shape doesnt match the image shape.")







