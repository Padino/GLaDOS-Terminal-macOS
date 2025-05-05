# GLaDOS-Terminal, Author LuckeyDuckey
# Edited by Padino for running on MacOS

print("Setting up, please wait.\n")

import pygame, sys, math, os, time, random, json
from pygame.locals import *

import moderngl as mgl
from array import array

import numpy as np

# Remove debug prints
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

# macOS specific setup
import platform
is_macos = platform.system() == 'Darwin'
is_apple_silicon = is_macos and platform.machine() == 'arm64'

if is_macos:
    # Enable high DPI and retina display support
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
    os.environ['SDL_VIDEO_WINDOW_POS'] = '100,100'  # Position window at 100,100
    pygame.display.set_allow_screensaver(True)
    # Ensure window appears in foreground on macOS
    if is_apple_silicon:
        os.environ['SDL_VIDEO_CENTERED'] = '1'

Font = pygame.font.Font("Fonts/1977-Apple2.ttf", 15)
FontSize, Color = [11, 21], [230, 125, 15]

Resolution = (104 * FontSize[0], 47 * FontSize[1])
# Use a standard display without OpenGL for better compatibility
Screen = pygame.display.set_mode(Resolution)
Display = pygame.Surface(Resolution).convert_alpha()
Display.fill((0, 0, 0, 255))  # Start with solid black background

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

# Skip OpenGL on macOS due to compatibility issues with Apple Silicon
USE_OPENGL = not is_apple_silicon

if USE_OPENGL:
    # Create appropriate context based on platform
    try:
        # Try standalone mode first
        Context = mgl.create_context(standalone=True)
    except Exception as e:
        try:
            # Fall back to using GLFW (more compatible with macOS)
            import glfw
            glfw.init()
            glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
            window = glfw.create_window(1, 1, "", None, None)
            glfw.make_context_current(window)
            Context = mgl.create_context()
        except Exception as e2:
            # Last resort - try without any requirements
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

    try:
        Program = Context.program(vertex_shader=VertexShader, fragment_shader=FragmentShader)
        RenderObject = Context.vertex_array(Program, [(QuadBuffer, "2f 2f", "vert", "texcoord")])
    except Exception as e:
        USE_OPENGL = False  # Fallback to standard rendering
else:
    # Silently skip OpenGL on Apple Silicon
    pass

## Functions and classes ###########################################################################

def SurfaceToTexture(Surface):
    if not USE_OPENGL:
        return Surface  # Just return the surface if not using OpenGL
    
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
try:
    pygame.mixer.music.load(os.path.join(os.getcwd(), "Sounds/ComputerAmbient.mp3"))
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(Settings["SoundEffectVolume"])
except Exception:
    pass  # Silently continue if sound fails

# Play boot sound
try:
    ComputerBootSound.play()
except Exception:
    pass  # Silently continue if sound fails

try:
    while True:
        try:
            # Set fps
            Clock.tick(FPS)

            # Update delta time
            DeltaTime = time.time() - LastTime
            LastTime = time.time()

            Time += DeltaTime
            
            # Update window title with time to make it easier to find
            pygame.display.set_caption("GLaDOS-Terminal")
            
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

            try:
                if USE_OPENGL:
                    # Use OpenGL rendering when available
                    DisplayTexure = SurfaceToTexture(pygame.transform.flip(Display, False, True))
                    DisplayTexure.use(0)
                    Program["PygameTexture"] = 0
                    
                    Program["Time"] = Time

                    RenderObject.render(mode=mgl.TRIANGLE_STRIP) # Call render function

                    # Update pygame window
                    pygame.display.flip()

                    # Release textures to avoid memory leaks
                    DisplayTexure.release()
                else:
                    # Use standard pygame rendering as fallback
                    Screen.blit(Display, (0, 0))
                    pygame.display.flip()
            except Exception:
                break

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
            
        except Exception:
            break
            
except KeyboardInterrupt:
    pass
except Exception:
    pass
finally:
    pygame.quit()
    sys.exit()
