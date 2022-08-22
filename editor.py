from tkinter import *
from tkinter import ttk, colorchooser, filedialog
from PIL import Image, ImageTk, ImageDraw
import io
import numpy as np
import os
import glob
# import skimage.io as ski_io

# from PIL import ImageGrab


class main:
    def __init__(self,master):
        self.master = master
        self.color_fg = '#ff0000'
        self.color_bg = 'white'
        self.img = None
        self.old_x = None
        self.old_y = None
        self.penwidth = 5
        self.eraser = False
        self.w = 300
        self.h = 300
        self.frame = 0
        self.nframes = 10
        self.frameData = {}
        self.icons = {}
        self.folder_name = None

        self.drawWidgets()
    
        

        # eraser tool
        if self.eraser == False:
            self.c.bind('<B1-Motion>',self.paint)
            self.c.bind('<ButtonRelease-1>',self.reset)
            
        else:
            self.c.bind('<B1-Motion>',self.paint)
            self.c.bind('<ButtonRelease-1>',self.reset)
        

    def paint(self,e):
        if self.old_x and self.old_y:
            self.c.create_line(self.old_x,self.old_y,e.x,e.y,width=self.penwidth,fill=self.color_fg,capstyle=ROUND,smooth=True)
            self.draw.line([(self.old_x, self.old_y),(e.x,e.y)], width=self.penwidth, fill=self.color_fg)
        self.old_x = e.x
        self.old_y = e.y

    def reset(self,e):
        self.old_x = None
        self.old_y = None      

    
    def save(self):
        filename = "temp/{}/file_{}.png".format(self.folder_name, self.frame)

        print(self.frameData[int(self.frame)])
        self.frameData[self.frame].save(filename, 'PNG')
        # print(np.asarray(self.frameData[self.frame]))
        
        print("saved")
    
    def import_file(self):
        self.file = filedialog.askopenfilename(initialdir = os.getcwd(),title = "Select file",filetypes = (("gif files","*.gif"),("jpeg files","*.jpg"),("all files","*.*")))
        self.folder_name = self.file.split("\\")[-1].split("/")[-1]
        dir_exist = True
        try:
            os.mkdir("./temp/{}".format(self.folder_name))
            dir_exist = False
        except:
            pass
        self.nframes = Image.open(self.file).n_frames

        self.controls = Frame(self.master,padx = 5,pady = 5)
        Label(self.controls, text='Frame',font=('',10)).grid(row=0,column=0)
        self.slider = Scale(self.controls,width=15, sliderlength=15, from_= 0, to = self.nframes-1, command=self.changeFrame, activebackground='#1065BF', sliderrelief='flat', orient=HORIZONTAL)
        self.slider.set(self.frame)
        self.slider.grid(row=0,column=1,ipadx=30)
        self.controls.pack()
        
        self.img = PhotoImage(file=self.file, format= 'gif - {}'.format(self.frame))
        self.w, self.h = self.img.width(),  self.img.height()
        self.c.config(width=self.w, height=self.h)
        self.c.create_image(0,0, anchor=NW, image = self.img)

        for i in range(self.nframes):
            self.frameData[i] = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
            if dir_exist == False:
                filename = "temp/{}/file_{}.png".format(self.folder_name, i)
                self.frameData[self.frame].save(filename, 'PNG')
            

        self.draw = ImageDraw.Draw(self.frameData[self.frame])
        self.slider = Scale(self.controls,width=15, sliderlength=15, from_= 0, to = self.nframes-1, command=self.changeFrame, activebackground='#1065BF', sliderrelief='flat', orient=HORIZONTAL)
        
    def import_raw(self):
        self.c2 = Canvas(self.master,width=300,height=300,bg=self.color_bg)
        self.c2.pack() #fill=BOTH,expand=False

        self.file2 = filedialog.askopenfilename(initialdir = os.getcwd(),title = "Select file",filetypes = (("gif files","*.gif"),("jpeg files","*.jpg"),("all files","*.*")))
        self.img2 = PhotoImage(file=self.file2, format= 'gif - {}'.format(self.frame))
        self.w, self.h = self.img.width(),  self.img.height()
        self.c2.config(width=self.w, height=self.h)
        self.c2.create_image(0,0, anchor=NW, image = self.img2)



    def clear(self):
        self.c.delete(ALL)

        self.img = PhotoImage(file=self.file, format= 'gif - {}'.format(self.frame))
        self.w, self.h = self.img.width(),  self.img.height()
        self.c.config(width=self.w, height=self.h)
        self.c.create_image(0,0, anchor=NW, image = self.img)

        self.frameData[self.frame] = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.frameData[self.frame])

    def change_fg(self):
        self.color_fg=colorchooser.askcolor(color=self.color_fg)[1]
        

    def change_bg(self):
        self.color_bg=colorchooser.askcolor(color=self.color_bg)[1]
        self.c['bg'] = self.color_bg
    
    def changeFrame(self,e):
        self.save()
        self.frame = int(e)

        self.img = PhotoImage(file=self.file, format= 'gif - {}'.format(self.frame))
        self.w, self.h = self.img.width(),  self.img.height()
        self.c.config(width=self.w, height=self.h)
        self.c.create_image(0,0, anchor=NW, image = self.img)

        annotationFile = "temp/{}/file_{}.png".format(self.folder_name, e)
        if os.path.isfile(annotationFile):
            self.img_annot = PhotoImage(file=annotationFile)
            self.c.create_image(0,0, anchor=NW, image = self.img_annot)
            print("annotation found")
            
        
        self.draw = ImageDraw.Draw(self.frameData[self.frame])

        self.img2 = PhotoImage(file=self.file2, format= 'gif - {}'.format(self.frame))
        self.c2.config(width=self.w, height=self.h)
        self.c2.create_image(0,0, anchor=NW, image = self.img2)
        
    def setAdd(self):
        self.color_fg = '#800080' # rgb(128,0,128)

    def setSubtract(self):
        self.color_fg = '#f0a400' # rgb(240,165,0)

    def setPen(self):
        self.color_fg = '#ff0000'
    
    def setEraser(self):
        self.color_fg = '#0000FF'

    def setMerge(self):
        self.color_fg = '#BFFF00'

    def changeSize(self, e):
        self.penwidth = int(e)

    def drawWidgets(self):
        #### TOOLBAR
        self.toolbar = Frame(self.master)
        self.toolbar.pack(fill=X)

        for i in glob.glob("assets/icons/*.png"):
            pathfile = i
            i = os.path.basename(i)
            name = i.split(".")[0]
            self.icons[name] = PhotoImage(file=pathfile).subsample(2)

        b1 = Button(
            self.toolbar,
            relief=FLAT,
            compound = LEFT,
            command=self.setPen,
            image=self.icons["pen"],
            height = 30, 
            width = 30)
        b1.pack(side=LEFT, padx=5, pady=0)

        b2 = Button(
            self.toolbar,
            relief=FLAT,
            compound = LEFT,
            command=self.setEraser,
            image=self.icons["eraser"],
            height = 30, 
            width = 30)
        b2.pack(side=LEFT, padx=5, pady=0)

        b3 = Button(
            self.toolbar,
            relief=FLAT,
            compound = LEFT,
            command=self.setMerge,
            image=self.icons["merge"],
            height = 30, 
            width = 30)
        b3.pack(side=LEFT, padx=5, pady=0)

        b4 = Button(
            self.toolbar,
            relief=FLAT,
            compound = LEFT,
            command=self.setAdd,
            image=self.icons["add"],
            height = 30, 
            width = 30)
        b4.pack(side=LEFT, padx=5, pady=0)

        b5 = Button(
            self.toolbar,
            relief=FLAT,
            compound = LEFT,
            command=self.setSubtract,
            image=self.icons["subtract"],
            height = 30, 
            width = 30)
        b5.pack(side=LEFT, padx=5, pady=0)

        self.brushControls = Frame(self.master,padx = 5,pady = 0)
        Label(self.brushControls, text='Brush Size',font=('',10)).grid(row=0,column=0)
        self.brushSlider = Scale(self.brushControls,width=20, sliderlength=15, from_= 1, to = 30, command=self.changeSize, activebackground='#1065BF', sliderrelief='flat', orient=HORIZONTAL)
        self.brushSlider.grid(row=0,column=1,ipadx=30)
        self.brushControls.pack()
        self.brushSlider.set(self.penwidth)

        self.c = Canvas(self.master,width=300,height=300,bg=self.color_bg)
        self.c.pack() #fill=BOTH,expand=False

        self.frameData[self.frame] = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.frameData[self.frame])


        menu = Menu(self.master)
        self.master.config(menu=menu)
        filemenu = Menu(menu)
        menu.add_cascade(label='File...',menu=filemenu)
        filemenu.add_command(label='Save',command=self.save)
        filemenu.add_command(label='Import Raw Segmentation',command=self.import_file)
        filemenu.add_command(label='Import Original Images',command=self.import_raw)
        # colormenu = Menu(menu)
        # menu.add_cascade(label='Colors',menu=colormenu)
        # colormenu.add_command(label='Brush Color',command=self.change_fg)
        # colormenu.add_command(label='Background Color',command=self.change_bg)
        optionmenu = Menu(menu)
        menu.add_cascade(label='Options',menu=optionmenu)
        optionmenu.add_command(label='Clear Annotations',command=self.clear)
        
        

if __name__ == '__main__':
    root = Tk()
    main(root)
    root.title('Membrane editor')
    root.resizable(False, False)

    
    
    
    root.mainloop()


#To Do list:
# - Different color buttons for different effects. e.g. merge segmentations; pen draw
# - Pen width tool
# - Allow arrow keys to change frame
# - Undo/redo if possible (probably not)
# - Warnings
# - Make the export work properly
# - Save specific temp file
# - second canvas with the actual images 

# - Nuclear segmentation 
# - Work on larger scale dataset 
# - With nuclear tracks, crop out from the image (of the cell) {to assist with segmentation} so that the entire nucleus would be located within it 