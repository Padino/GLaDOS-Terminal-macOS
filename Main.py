# GLaDOS-Terminal, Author LuckeyDuckey

print("Setting up, please wait.\n")

import pygame, sys, math, os, time, random, json
from pygame.locals import *

import moderngl as mgl
from array import array

import numpy as np

from Scripts.TextInput import TextInput
from Scripts.TextProcessing import TextProcessing
from Scripts.LargeLanguageModel import LargeLanguageModel
from Scripts.TextToSpeech import TextToSpeech

# Load in settings
with open("Settings.json", "r") as File:
    Settings = json.loads(File.read())

GeneratorLLM = LargeLanguageModel(Settings["ModelName"], Settings["SystemPrompt"])
GeneratorTTS = TextToSpeech(
    Settings["VoiceModels"]["ModelNameHifigan"], Settings["VoiceModels"]["ModelNameTacotron2"],
    Settings["VoiceModels"]["ModelIDHifigan"], Settings["VoiceModels"]["ModelIDTacotron2"], 0.75
)

## Pygame Setup Bits ###############################################################################

pygame.init()
pygame.display.set_caption("GLaDOS-Terminal")

Font = pygame.font.Font("Fonts/1977-Apple2.ttf", 15)
FontSize, Color = [11, 21], [230, 125, 15]

Resolution = (104 * FontSize[0], 47 * FontSize[1])
Screen = pygame.display.set_mode(Resolution, flags=pygame.OPENGL | pygame.DOUBLEBUF)
Display = pygame.Surface(Resolution).convert_alpha()

# Set window icon
IconImage = pygame.transform.scale(pygame.image.load(os.path.join(os.getcwd(), "Images/Icon.png")), (360, 360)).convert_alpha()
pygame.display.set_icon(IconImage)

Clock, LastTime = pygame.time.Clock(), time.time()
FPS, Time = 30, 0

HeldKeys = {}

# Init audio stuff
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.mixer.set_num_channels(64)

# Load in all sounds
ComputerBootSound = pygame.mixer.Sound(os.path.join(os.getcwd(), "Sounds/ComputerBoot.mp3"))
KeyboardPressedSound = pygame.mixer.Sound(os.path.join(os.getcwd(), "Sounds/KeyboardPressed.mp3"))

ComputerBootSound.set_volume(Settings["SoundEffectVolume"])
KeyboardPressedSound.set_volume(Settings["SoundEffectVolume"])

# init scrap for clipboard handling
pygame.scrap.init()
pygame.scrap.set_mode(pygame.SCRAP_CLIPBOARD)

# Allow keys to repeat and allow for text inputs
pygame.key.set_repeat(500, 33)
pygame.key.start_text_input()

## OpenGL Setup Bits ###############################################################################

Context = mgl.create_context()

QuadBuffer = Context.buffer(data=array("f", [
    # Position (x, y), uv coords (x, y)
    -1.0, 1.0, 0.0, 1.0,  # Topleft
    1.0, 1.0, 1.0, 1.0,   # Topright
    -1.0, -1.0, 0.0, 0.0, # Bottomleft
    1.0, -1.0, 1.0, 0.0   # Bottomright
]))

with open(f"Shaders/Vertex.glsl") as file:
    VertexShader = file.read()

with open(f"Shaders/Fragment.glsl") as file:
    FragmentShader = file.read()

Program = Context.program(vertex_shader=VertexShader, fragment_shader=FragmentShader)
RenderObject = Context.vertex_array(Program, [(QuadBuffer, "2f 2f", "vert", "texcoord")])

## Functions and classes ###########################################################################

def SurfaceToTexture(Surface):
    Texure = Context.texture(Surface.get_size(), 4) # Innit texture
    Texure.filter = (mgl.NEAREST, mgl.NEAREST) # Set properties
    Texure.repeat_x, Texure.repeat_y = False, False # Make texture not repeat
    Texure.swizzle = "BGRA" # Set format
    Texure.write(Surface.get_view("1")) # Render surf to texture
    Texure.build_mipmaps() # Generate mipmaps
    return Texure # Return OpenGL texture

InputProcesser = TextInput()
TextProcesser = TextProcessing()

TextProcesser.AddConversatoinText(f"Welcome to GLaDOS Terminal v2.8.5", False)

## Main game loop ##################################################################################

# Play background ambience sound and set it to repeat
pygame.mixer.music.load(os.path.join(os.getcwd(), "Sounds/ComputerAmbient.mp3"))
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(Settings["SoundEffectVolume"])

# Play boot sound
ComputerBootSound.play()

while True:

    # Set fps
    Clock.tick(FPS)

    # Update delta time
    DeltaTime = time.time() - LastTime
    LastTime = time.time()

    Time += DeltaTime
    
    ## Pygame screen rendering #####################################################################

    # Fade out previous text
    Fade = pygame.Surface(Resolution).convert_alpha()
    Fade.fill([max(1, Value * 0.1) for Value in Color])
    Display.blit(Fade, (0,0), special_flags=BLEND_RGB_SUB)

    Lines = TextProcesser.GetMainText(InputProcesser.GetInputText()) if Time > 5 else TextProcesser.GetLoadingText()

    # Draw new text
    for Line, Text in enumerate(Lines):
        for Count, Letter in enumerate(Text):
            Display.blit(Font.render(Letter, True, [230, 125, 15]), [Count * FontSize[0], Line * FontSize[1]])
            
    ## OpenGL section ##############################################################################

    # Pass in pygame display texture
    DisplayTexure = SurfaceToTexture(pygame.transform.flip(Display, False, True))
    DisplayTexure.use(0)
    Program["PygameTexture"] = 0
    
    Program["Time"] = Time

    RenderObject.render(mode=mgl.TRIANGLE_STRIP) # Call render function

    # Update pygame window
    pygame.display.flip()

    # Release textures to avoid memory leaks
    DisplayTexure.release()

    ## General inputs handling #####################################################################

    # Check for completed inference
    Processed, Response = GeneratorLLM.CheckResponse()
    
    if Processed:
        # Add AI response to conversation visuals
        TextProcesser.AddConversatoinText(f"GLaDOS > {Response}", True)

        # Speak response
        GeneratorTTS.StartInference(Response)

    for Event in pygame.event.get():

        if Time > 5:
            if InputProcesser.Event(Event, not (GeneratorLLM.IsProcessing or GeneratorTTS.IsProcessing)):

                # Get AI response
                ResponseAI = GeneratorLLM.StartInference(InputProcesser.Text)
                
                # Add user input to conversation visuals
                TextProcesser.AddConversatoinText(f"User > {InputProcesser.Text}", True)
                
                InputProcesser.Text = ""
        
        if Event.type == QUIT:
            pygame.quit()
            sys.exit()

        elif Event.type == pygame.KEYDOWN:

            # Check if this is the initial press of the key
            if Event.key not in HeldKeys:
                KeyboardPressedSound.play()
                HeldKeys[Event.key] = True
            
            if Time > 5:
                if Event.key == K_UP:
                    TextProcesser.Scroll(-1)
                    
                elif Event.key == K_DOWN:
                    TextProcesser.Scroll(1)

        elif Event.type == pygame.KEYUP:
            # Remove the key from HeldKeys
            HeldKeys.pop(Event.key)
