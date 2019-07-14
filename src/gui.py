from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl
from PyQt5.QtQuick import QQuickImageProvider

import utils.fp as fp
from ImListModel import ImListModel
import imageio as io
import config
import state
import core

# TODO: refactor img-providers into 1 class 
#       parameterized by io.load(path,xxx)
class ImageUpdater(QQuickImageProvider):
    def __init__(self):
        super(ImageUpdater, self).__init__(
            QQuickImageProvider.Image) 

    def requestImage(self, path, size):
        img = io.load(path)
        return img, img.size()

class MaskProvider(QQuickImageProvider):
    def __init__(self):
        super(MaskProvider, self).__init__(
            QQuickImageProvider.Image) 

    def requestImage(self, path, size):
        img = io.load(path)
        print(img, img.size(),'------------------- *')
        return img, img.size()
        '''
        #cv2.imshow('mask', iu.imread(mask_path)); cv2.waitKey(0)
        # TODO: mask have to save in bgr..
        mask = iu.imread(mask_path) # bgra
        mask = wb2rb(mask)
        mask = iu.np_bgra2qimg(mask)
        #mask = QImage(mask_path)
        '''

class MainWindow(QObject):
    imageUpdate = pyqtSignal(str, arguments=['path']) 
    warning = pyqtSignal(str, arguments=['msg'])
    maskProvide = pyqtSignal(str, arguments=['path']) 

    def __init__(self,engine):
        QObject.__init__(self)

        engine.rootContext().setContextProperty(
            config.MAIN_CONTEXT_NAME, self
        )
        engine.addImageProvider(
            'imageUpdater', ImageUpdater()
        )
        engine.addImageProvider(
            'maskProvider', MaskProvider()
        )

        self.im_model = ImListModel()
        engine.rootContext().setContextProperty(
            'ImModel', self.im_model
        )

        engine.load(config.MAIN_QML)
        self.window = engine.rootObjects()[0]

    def update_gui(self):
        now_imgpath = state.now_image()
        if now_imgpath:
            self.imageUpdate.emit(now_imgpath)
            self.maskProvide.emit(state.now_mask())
            self.im_model.update()

    #---------------------------------------------------
    @pyqtSlot(QUrl)
    def open_project(self, dir_url):
        dirpath = dir_url.toLocalFile()

        dir_type = state.dir_type(dirpath)
        if dir_type == config.UNSUPPORT_DIR: 
            self.warning.emit(
                config.WARN_MSGS[config.UNSUPPORT_DIR]
            )
            return dir_type # for test
        if dir_type == config.FLAT_IMGDIR:
            #TODO: create project directory structure
            #      and then copy images into 'images'
            #      and then reset dirpath
            #      and then below: use project directory
            self.warning.emit(
                config.WARN_MSGS[config.FLAT_IMGDIR]
            )
        else:
            state.set_project(dirpath)
            self.update_gui()

        return dir_type # for test

    @pyqtSlot()
    def display_next(self):
        state.next()
        self.update_gui()

    @pyqtSlot()
    def display_prev(self):
        state.prev()
        self.update_gui()

    @pyqtSlot(int)
    def display(self, index):
        state.cursor(index)
        self.update_gui()

    #---------------------------------------------------
    @pyqtSlot()
    def gen_segmap(self):
        imgpath = state.now_image()
        if imgpath is None: return None

        segmap = fp.go(
            imgpath,
            lambda p: io.load(p,io.NDARR),
            core.segmap
        )
        io.save(state.now_mask(), segmap)
        # make bg(black) transparent qt img
        return segmap


