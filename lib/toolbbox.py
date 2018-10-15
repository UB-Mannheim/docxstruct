from os import path
import numpy as np
from PIL import Image
from tesserocr import PyTessBaseAPI, RIL, iterate_level

class ToolBBOX(object):
    """ This library works with bbox on the original image -
    - Snip the bbox out of the image
    - OCR the snippet with tesseract gives text and bbox per word and confidences per char
    - Store the snippet """

    def __init__(self):
        self.bbox = None
        self.imgpath = None
        self.imgname = None
        self.ftype = None
        self.fname = None
        self.img = None
        self.shape = None
        self.snippet = None
        self.ocr = {"bbox":None,"text":None,"charconf":None}
        self.__ocr_settings = {"lang":"akf3","psm":6,"oem":3}


    def imread(self, imgpath):
        """Loads the image with PIL-Lib"""
        try:
            self.imgpath = imgpath
            self.imgname = path.basename(imgpath)
            self.ftype = self.imgname.split(".")[-1]
            if self.ftype.lower() not in ["jpg", "png", "bmp", "gif", "tiff"]:
                raise NameError
            self.img = Image.open(f"{self.imgpath}")
            self.snippet = self.img
            self.shape = list(self.img.tile[0][1][:2]+self.img.tile[0][1][4:1:-1])
            self.bbox = self.shape
        except IOError:
            print(f"cannot open {self.imgpath}")
        except NameError:
            print(f"The image filetype {self.ftype} is not supported!")
        return True

    def save_snippet(self, path:str):
        """Saves the snippet"""
        try:
            if self.imgname is None:
                raise NameError
            bboxstr = "_".join(str(bboxval) for bboxval in self.bbox)
            self.fname = path + self.imgname.split(".")[0] + "bbox_" + bboxstr +  "." + ".".join(self.imgname.split(".")[1:])
            self.snippet.save(self.fname, self.snippet)
        except NameError:
            print("Please load an image first.")
        except:
            print(f"{self.fname} could not be stored.")
        return True

    def snip(self, bbox:list):
        """Snip the bboxarea out of the image"""
        try:
            if self.img is None:
                raise NameError
            if all(np.less(bbox[:2],self.shape[:2])) or all(np.greater_equal(bbox[2:4],self.shape[2:4])):
                raise ValueError
            if not isinstance(bbox,list) or len(bbox) != 4:
                raise TypeError
            if bbox != self.bbox:
                self.bbox = bbox
                self.snippet = self.img.crop(bbox)
        except TypeError:
            print("The bbox has not the right type or format.")
        except NameError:
            print("Please load an image first.")
        except ValueError as E:
            print(f"The bbox shape doesnt match the image shape. {E}")
        except Exception as E:
            print(E)
        return True

    @property
    def ocr_settings(self):
        return self.__ocr_settings

    @ocr_settings.setter
    def ocr_settings(self, lang=None,psm=None,oem=None):
        """Set the parameter from tesseracts"""
        if lang is not None:
            self.__ocr_settings["lang"] = lang
        if psm is not None:
            self.__ocr_settings["psm"] = psm
        if oem is not None:
            self.__ocr_settings["oem"] = oem
        return True

    def snippet_to_text(self):
        """Performs tesseract on the snippet"""
        try:
            if self.bbox is None:
                raise ValueError
            with PyTessBaseAPI(**self.ocr_settings) as api:
                api.SetImage(self.snippet)
                api.Recognize()
                ri = api.GetIterator()
                conf = []
                self.ocr["text"] = []
                self.ocr["charconf"] = []
                self.ocr["bbox"] = []
                for r in iterate_level(ri, RIL.SYMBOL):
                    if self.ocr["text"] == []:
                        self.ocr["text"].append(r.GetUTF8Text(RIL.WORD))
                        self.ocr["bbox"].append(r.BoundingBoxInternal(RIL.WORD))
                    if self.ocr["text"][-1] != r.GetUTF8Text(RIL.WORD):
                        self.ocr["text"].append(r.GetUTF8Text(RIL.WORD))
                        self.ocr["bbox"].append(r.BoundingBoxInternal(RIL.WORD))
                        self.ocr["charconf"].append(conf)
                        conf = []
                    conf.append(r.Confidence(RIL.SYMBOL))
                if conf != "":
                    self.ocr["charconf"].append(conf)
        except ValueError:
            print("Please first set the bbox value with snip_bbox.")
        return True







