#!/usr/bin/env python3

"""DrawCam lets you make simple drawings with a physical object and your webcam!

This program is designed to run in a linux environment
using python 3.4.x and pygame 1.9.2a0
"""

from sys import exit
import pygame
import pygame.camera
import pygame.freetype
from pygame.locals import *

__author__ = "Kelvin Liu"
__version__ = "1.1.0"
__email__ = "kelvin@thekelvinliu.com"

class DrawCam:
    """DrawCam class implements necessary methods to allow physical drawing"""
    def __init__(self):
        """Constructs DrawCam object and non-pygame related instance variables"""
        #pygame
        self.pygame_setup()
        #track camera calibration
        self.calibrated = False
        #list of object positions
        self.loc_list = []
        #index for loc_list
        self.loc_ind = 0

    def pygame_setup(self):
        """Initializes pygame and sets up pygame related instance vairables"""
        pygame.init()
        pygame.camera.init()
        #size of pygame window
        self.size = (640,480)
        #main surface
        self.screen = pygame.display.set_mode(self.size,0)
        #create surface for camera
        self.sight = pygame.surface.Surface(self.size,0)
        #create surface for drawings
        self.trace = pygame.surface.Surface(self.size,0)
        #create surface for text
        self.info = pygame.surface.Surface(self.size,0)
        #create font
        self.words = pygame.freetype.SysFont('FreeMono', 25, True, False)
        self.words.origin = True
        #set window title
        pygame.display.set_caption("DrawCam")
        #set colorspace
        self.cs = "RGB"
        #find cameras
        camlst = pygame.camera.list_cameras()
        if not camlst:
            raise ValueError("No cameras detected.")
            exit()
        else:
            #create and start camera with first camera in camlst
            self.cam = pygame.camera.Camera(camlst[0], self.size, self.cs)
            self.cam.start()

    def stop(self):
        """Stops pygame camera for graceful shutdown"""
        self.cam.stop()

    #get image from camera
    def cam_stream(self):
        """Blits what the camera sees to a surface"""
        if self.cam.query_image():
            self.sight = self.cam.get_image(self.sight)
            self.sight = pygame.transform.flip(self.sight, True, False)
            self.screen.blit(self.sight, (0,0))

    #update display screen
    def update(self):
        """Updates the pygame screen, used for DrawCam.update()"""
        pygame.display.update()

    #draw square
    def draw_sq(self):
        """Draws a square in the middle of the screen"""
        self.sq = pygame.draw.rect(self.screen, (255,0,0), (305,255,30,30), 2)

    #get color within square
    def get_color(self):
        """Find average color within self.sq"""
        self.sq_color = pygame.transform.average_color(self.sight, self.sq)
        #set calibration to true
        self.calibrated = True
        #briefly show color in top left corner
        self.screen.fill(self.sq_color, (0,0,50,50))
        pygame.display.update()
        pygame.time.delay(500)

    def make_mask(self):
        """Masks all other colors to make tracking easier"""
        #get latest image
        self.sight = self.cam.get_image(self.sight)
        self.sight = pygame.transform.flip(self.sight, True, False)
        #threshold with self.sq_color
        mask = pygame.mask.from_threshold(self.sight, self.sq_color, (30,30,30))
        self.screen.blit(self.sight, (0,0))
        #target only largest group of sq_color
        #mask.connected_component()
        #make sure the target is not just noise/mistaken
        if mask.count() > 500:
            #find center and draw a circle and append to self.loc_list
            coord = mask.centroid()
            pygame.draw.circle(self.screen, (255,0,255), coord, 5)
            pygame.display.update()
            self.loc_list.append(coord)

    def better_path(self):
        """Draws a path using coordinates in self.loc_list"""
        self.trace.set_colorkey((0,0,0))
        #if the object has moved (location list has mutliple entries)
        if self.loc_ind > 0:
            #calculates change in x and y
            dx = self.loc_list[self.loc_ind][0]-self.loc_list[self.loc_ind-1][0]
            dy = self.loc_list[self.loc_ind][1]-self.loc_list[self.loc_ind-1][1]
            #use higher value of dx or dy
            dist = max(abs(dx),abs(dy))
            #draw smooth path using many circles
            for pix in range(dist):
                #calculate new x and y values
                x = int(self.loc_list[self.loc_ind - 1][0] + pix/dist * dx)
                y = int(self.loc_list[self.loc_ind - 1][1] + pix/dist * dy)
                pygame.draw.circle(self.trace, self.sq_color, (x, y), 5)
        #add one to location index to get ready for next coord
        self.loc_ind += 1
        #blit to screen
        self.screen.blit(self.trace, (0,0))

    #clear drawings
    def clear_path(self):
        """Clears drawings on screen"""
        #clear surface
        self.trace.fill((0,0,0),(0,0,640,480))
        self.screen.blit(self.trace,(0,0))
        #reset self.loc_list and self.loc_ind
        self.loc_list = []
        self.loc_ind = 0
        #update
        pygame.display.update()

    #renders information text to info surface
    def render_help(self):
        """Renders helpful text onto the screen"""
        text = ["Welcome to the help screen!", \
                "", \
                "Key            Action", \
                "'h'            Toggle information", \
                "'space'        Calibrate camera", \
                "'del'          Clear drawings", \
                "'backspace'    Clear drawings", \
                "'esc'          Exit program"]
        #use first line as reference for center
        dims = self.words.get_rect(text[0])
        #x value to center first line, all other lines will be alinged to this
        x_set = int((self.size[0] - dims[2]) / 2)
        y_set = 50
        #set a gray background
        self.info.fill((150,150,150))
        #render each line of text
        for line in text:
            self.words.render_to(self.info, (x_set,y_set), line, (255,255,255))
            y_set += (dims[3] + 5)

    def toggle_help(self):
        """Toggles the help text"""
        self.render_help()
        self.info.set_colorkey((0,0,0))
        #show help text until user presses 'h' or exits
        self.helping = True
        while self.helping:
            for event in pygame.event.get():
                if event.type == QUIT or \
                  (event.type == KEYDOWN and event.key == K_ESCAPE):
                    self.helping = False
                    self.cam.stop()
                    pygame.quit()
                    exit()
                if event.type==KEYDOWN and event.key==K_h:
                    self.info.fill((0,0,0),(0,0,640,480))
                    self.screen.blit(self.info, (0,0))
                    self.helping = False
            #blit and update
            self.screen.blit(self.info, (0,0))
            pygame.display.update()

def main():
    #create DrawCam object
    camera = DrawCam()
    #pygame event loop
    while True:
        for event in pygame.event.get():
            #if user presses closes window, quit program
            if event.type == QUIT:
                #stop camera, quit pygame, and exit
                camera.stop()
                pygame.quit()
                exit()
            #if user presses key
            if event.type == KEYDOWN:
                #if 'esc' is pressed, quit (same as QUIT event)
                if event.key == K_ESCAPE:
                    camera.stop()
                    pygame.quit()
                    exit()
                #if 'space' is pressed, start calibration
                #make sure the camera is not already calibrated
                if event.key == K_SPACE and not camera.calibrated:
                    camera.get_color()
                #if 'del' or 'backspace' is pressed, clear screen
                if event.key == K_BACKSPACE or event.key == K_DELETE:
                    camera.clear_path()
                #if 'h' is pressed, show controls
                if event.key == K_h:
                    camera.toggle_help()
        #stream what camera sees
        camera.cam_stream()
        #draw a square if camera has not been calibrated
        if not camera.calibrated:
            camera.draw_sq()
        #otherwise mask the average color and start drawing
        else:
            camera.make_mask()
            camera.better_path()
        #update screen
        camera.update()

#run DrawCam
if __name__ == '__main__':
    main()
