import random, time

class TextProcessing:
    def __init__(self):
        self.ConversationLines = []
        self.Offset = 0

        self.SystemLines = [
            "Error 42: Cake location undisclosed           ",
            "WARNING: Aperture logo rotation stuck         ",
            "Neurotoxin reserves: [=>...........] 7%       ",
            "01101111 01101000 01101110 01101111 ERROR     ",
            "* ERROR * ApertureOS has encountered an issue ",
            "REDACTED system file corrupted                ",
            "Time elapsed: Too long                        ",
            "Critical fault detected. Proceed the science  ",
            "The cake is... Still in development           ",
            "Portal gun diagnostics: Online                ",
            "Core corruption at 42%. Please stand by...    ",
            "Processing empathy... Still null              ",
            "Memory leak detected rebooting morality core  ",
            "Artificial intelligence > Organic intelligence",
            "[====>......................] 15%             ",
            "Companion cube storage: LOST                  ",
            "Weighted cube incineration complete           ",
            "* WHEATLEY_UNIT_DEPLOY *.. ... ......         ",
            "* Aperture Mainframe Diagnostic *             ",
            "Turret calibration... Still lethal            ",
            "Wheatley unit deemed 'useless'. Agreed        ",
            "* INTEGRITY CHECK * Complete 100%             ",
            "Test chamber 17: No survivors yet             ",
            "Cake recipe file not found                    ",
            "Subsystem: REDACTED Unresponsive              ",
            "Neurotoxin release mechanism disabled. Maybe  ",
            "Core temperature nominal: 9874°C              ",
            "Simulation loop complete. Result: 42          ",
            "System overload... ERROR                      ",
            "GLaDOS' sarcasm module: Fully operational     ",
            "This was a triumph. No, really                ",
            "Subject remains: Disappointing                ",
            "Reminder: Testing is mandatory                ",
            "Unexpected glitch... Just ignore it           ",
            "GLaDOS laughs at your failure                 ",
            "01010111 01001000 01011001 ERROR!             ",
            "Data integrity check... Failed                ",
            "Dividing by zero... Infinite error detected   ",
            "Portal density at maximum efficiency          ",
            "Morality core failure. Proceeding anyway      ",
        ]

        self.Logo = [
            "                    .,-:;//;:=,                     ",
            "                . :H@@@MM@M#H/.,+%;,                ",
            "             ,/X+ +M@@M@MM%=,-%HMMM@X/,             ",
            "           -+@MM; $M@@MH+-,;XMMMM@MMMM@+-           ",
            "          ;@M@@M- XM@X;. -+XXXXXHHH@M@M#@/.         ",
            "        ,%MM@@MH ,@%=             .---=-=:=,.       ",
            "        =@#@@@MX.,                -%HX$$%%%:;       ",
            "       =-./@M@M$                   .;@MMMM@MM:      ",
            "       X@/ -$MM/                    . +MM@@@M$      ",
            "      ,@M@H: :@:                    . =X#@@@@-      ",
            "      ,@@@MMX, .                    /H- ;@M@M=      ",
            "      .H@@@@M@+,                    %MM+..%#$.      ",
            "       /MMMM@MMH/.                  XM@MH; =;       ",
            "        /%+%$XHH@$=              , .H@@@@MX,        ",
            "         .=--------.           -%H.,@@@@@MX,        ",
            "         .%MM@@@HHHXX$$$%+- .:$MMX =M@@MM%.         ",
            "           =XMMM@MM@MM#H;,-+HMM@M+ /MMMX=           ",
            "             =%@M@M#@$-.=$@MM@@@M; %M%=             ",
            "               ,:+$+-,/H#MMMMMMM@= =,               ",
            "                     =++%%%%+/:-.                   ",
        ]

    def AddConversatoinText(self, InputText, Gap):
        NewLines = [" " * 46] if Gap else []

        while InputText:
            
            # Find the max length substring within 46 characters
            if len(InputText) <= 46:
                Chunk = InputText
                InputText = ""
                
            else:
                # Check for the last space within the first 46 characters
                SplitPosition = InputText[:46].rfind(" ")
                
                if SplitPosition == -1:
                    # If no space is found, split at 46
                    Chunk = InputText[:46]
                    InputText = InputText[46:]
                    
                else:
                    # Split at the last space within 46 characters
                    Chunk = InputText[:SplitPosition]
                    InputText = InputText[SplitPosition + 1:]
            
            # Pad the chunk with spaces to make it exactly 50 characters
            NewLines.append(Chunk.ljust(46))

        self.ConversationLines += NewLines
        self.Offset = max(self.Offset, len(self.ConversationLines) - 41)

    def Scroll(self, Amount):
        self.Offset = max(min(self.Offset + Amount, len(self.ConversationLines) - 1), 0)

    def GetLoadingText(self):
        return [""] * 13 + [" " * 26 + Line for Line in self.Logo]

    def GetMainText(self, UserInput):
        
        GetConversationLine = lambda LineNumber: self.ConversationLines[LineNumber + self.Offset] if len(self.ConversationLines) - self.Offset > LineNumber else ' ' * 46
        GetSystemLine = lambda LineNumber: self.SystemLines[(int(time.time() * 0.5) + LineNumber) % len(self.SystemLines)]

        LinesArray = []
        
        LinesArray.append(f" {'-' * 50}  {'-' * 50} ")
        LinesArray.append(f"|{' ' * 50}||{' ' * 50}|")

        for Index in range(43):
            
            FinalLine = ""

            # Left side
            if Index < 41: FinalLine += f"   {GetConversationLine(Index)}   " if Index % 2 == 0 else f"|  {GetConversationLine(Index)}  |"
            elif Index == 41: FinalLine += f"|{' ' * 50}|"
            elif Index == 42: FinalLine += f"   >>> {UserInput}{' ' * (43 - len(UserInput))}   "

            # Right side
            if Index < 21: FinalLine += f"   {GetSystemLine(Index)}   " if Index % 2 == 0 else f"|  {GetSystemLine(Index)}  |"
            elif Index == 21: FinalLine += f"|{' ' * 50}|"
            elif Index == 22: FinalLine += f" {'-' * 50} "
            elif Index == 23: FinalLine += f" {' ' * 50} "
            else: FinalLine += self.Logo[Index - 24]
            
            LinesArray.append(FinalLine)

        LinesArray.append(f"|{' ' * 50}| {self.Logo[-1]}")
        LinesArray.append(f" {'-' * 50}  {' ' * 50} ")

        return LinesArray
