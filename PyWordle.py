import os, random
from Scripts import utils

class Wordle:

    def __init__(self, **kwargs):
        if os.name=="nt": os.system("color") # Gets cmd working with ANSI escapes
        self.u = utils.Utils("PyWordle")
        self.word_list = self.load_word_list()
        self.colors = [
            "\u001b[43;1m {} \u001b[0m",    # yellow
            "\u001b[42;1m {} \u001b[0m",    # green
            "\u001b[48;5;240m {} \u001b[0m" # gray
        ]

    def load_word_list(self, custom_path = None):
        # Checks for the word list, loads it, makes sure there's only 5 alpha characters per word
        if custom_path:
            word_list_path = custom_path
        else:
            word_list_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"Scripts","WordList.txt")
        word_list_name = os.path.basename(word_list_path)
        self.u.head()
        print("")
        print("Checking for {}...".format(word_list_name))
        if not os.path.exists(word_list_path):
            print(" - Doesn't exist!  Aborting...")
            exit(1)
        print(" - Located")
        print("Loading {}...".format(word_list_name))
        try:
            with open(word_list_path,"r") as f:
                word_list = [x.strip().upper() for x in f.read().replace("\r","").split("\n") if len(x)]
        except Exception as e:
            print(" - Failed to load: {}".format(e))
            print(" - Aborting...")
            exit(1)
        print("Verifying word list...")
        only_alpha = [x for x in word_list if x.isalpha()]
        have_alpha = len(word_list)-len(only_alpha)
        if not have_alpha:
            print(" - No words containing non-alpha characters")
        else:
            print(" - {:,} word{} containing non-alpha characters removed".format(have_alpha,"" if have_alpha==1 else "s"))
        five_letters = [x for x in only_alpha if len(x)==5]
        not_five = len(only_alpha)-len(five_letters)
        if not not_five:
            print(" - All words have 5 letters")
        else:
            print(" - {:,} word{} with < 5 or > 5 letters removed".format(not_five,"" if not_five==1 else "s"))
        if not five_letters:
            print("No valid words loaded!  Aborting...")
            exit(1)
        print("Loaded {:,} word{} from {}.".format(len(five_letters),"" if len(five_letters)==1 else "s",word_list_name))
        return five_letters

    def check_guess(self,guess,target):
        # Compares the guess against the sequence
        right_right = [x for x in range(len(guess)) if guess[x] == target[x]]
        right_wrong = []
        letters = [guess[x] for x in right_right]
        for x in range(len(guess)):
            if x in right_right: continue # Skip correct guess indexes
            # Get a list of indexes that match our guess
            temp_check = [y for y in range(len(target)) if target[y] == guess[x] and not y in right_right]
            if temp_check and not x in right_wrong:
                # Make sure we don't set too many of the same letter
                if letters.count(guess[x]) < target.count(guess[x]):
                    right_wrong.append(x)
                    letters.append(guess[x])
        return (right_wrong,right_right)

    def pretty_print(self,guess,target):
        right_wrong,right_right = self.check_guess(guess,target)
        pretty = ""
        for i,x in enumerate(guess):
            index = 0 if i in right_wrong else 1 if i in right_right else -1
            pretty += self.colors[index].format(x)
        return pretty

    def check_all_guesses(self,guesses,target):
        rw = []
        rr = []
        for guess in guesses:
            w,r = self.check_guess(guess,target)
            rw.extend([x for x in w if not x in rw])
            rr.extend([x for x in r if not x in rr])
        return (rw,rr)

    def print_kb(self,guesses,target):
        rw = []
        rr = []
        ww = []
        for guess in guesses:
            w,r = self.check_guess(guess,target)
            rw.extend([guess[x] for x in w if not guess[x] in rw])
            rr.extend([guess[x] for x in r if not guess[x] in rr])
            ww.extend([x for x in guess if not x in target and not x in ww])
        rw = [x for x in rw if not x in rr] # Only retain the right-right
        rows = []
        for i,row in enumerate(("QWERTYUIOP","ASDFGHJKL","ZXCVBNM")):
            text = "" if i==0 else " "*2 if i==1 else " "*4
            for char in row:
                index = 0 if char in rw else 1 if char in rr else -1 if char in ww else None
                if index is None: text += " "+char+" "
                else:             text += self.colors[index].format(char)
            rows.append(text)
        print("\n".join(rows))

    def get_hint(self,guesses,target,hints_used):
        # Let's find out which we've guessed right, as well as which
        # are right letters, but in the wrong spots.
        rw_i = [] # Set empty lists for all indices and letters in the guess checks
        rw_l = []
        rr_i = []
        rr_l = []
        for guess in guesses:
            w,r = self.check_guess(guess,target)
            # Get the right letter/wrong spot indices and letters
            rw_i.extend([x for x in w if not x in rw_i])
            rw_l.extend([guess[x] for x in w if not guess[x] in rw_l])
            # Get the right letter/right spot indices and letters
            rr_i.extend([x for x in r if not x in rr_i])
            rr_l.extend([guess[x] for x in r if not guess[x] in rr_l])
        missing_letters = [x for x in target if not x in rr_l+rw_l]
        missing_indices = [x for x in range(len(target)) if not x in rr_i+rw_i]
        letter_hints    = [x for x in missing_letters if not x in hints_used]
        index_hints     = [x for x in missing_indices if not x in hints_used]
        hint_text = ""
        if not letter_hints and not index_hints:
            # We've given all the hints already - let's give the index hints
            # again - as we've already gone through the letters.
            index_hints = missing_indices
            # Let's also remove any indices from our hints_used to start over
            hints_used = [x for x in hints_used if not isinstance(x,int)]
        if letter_hints: # We can get a letter!
            hint = random.choice(letter_hints)
            hint_text = "The word contains: {}".format(self.colors[0].format(hint))
        else:
            hint = random.choice(index_hints)
            suffix = "th"
            h = hint+1
            if str(h)[-1]=="1" and str(h)[-2:]!="11": suffix = "st"
            if str(h)[-1]=="2" and str(h)[-2:]!="12": suffix = "nd"
            if str(h)[-1]=="3" and str(h)[-2:]!="13": suffix = "rd"
            hint_text = "The {:,}{} letter is: {}".format(h,suffix,self.colors[1].format(target[hint]))
        # Save the hint
        hints_used.append(hint)
        # Show the hint to the user
        self.u.head()
        print("")
        print(hint_text)
        print("")
        self.u.grab("Press [enter] to continue...")
        return hints_used

    def start_game(self,**kwargs):
        guesses     = kwargs.get("guesses",[])
        target      = kwargs.get("target",random.choice(self.word_list)).upper()
        max_guesses = kwargs.get("max_guesses",6)
        hard_mode   = kwargs.get("hard_mode",False)
        cheat_mode  = kwargs.get("cheat_mode",False)
        hints       = kwargs.get("hints",0) # Number of hints, < 0 for unlimited
        hints_used  = []
        while True:
            self.u.head()
            print("")
            if cheat_mode: print("({})\n".format(target))
            if guesses:
                # Print prior guesses here
                print("Guessed:\n")
                for i,g in enumerate(guesses,start=1):
                    print("{}. {}".format(i,self.pretty_print(g,target)))
                print("")
            print(" - {:,} {} -".format(
                max_guesses-len(guesses),
                "Guess Remains" if max_guesses-len(guesses)==1 else "Guesses Remain"
            ))
            print("")
            if isinstance(hints,int) and hints != 0:
                if hints < 0 or len(hints_used) < hints:
                    print("H. Get Hint{}".format("" if hints < 0 else " ({:,} Remain)".format(hints-len(hints_used))))
            print("M. Main Menu")
            print("Q. Quit")
            print("")
            self.print_kb(guesses,target)
            print("")
            guess = self.u.grab("Please enter a {:,} letter word:  ".format(len(target))).upper()
            if not len(guess): continue
            if guess == "Q": self.u.custom_quit()
            if guess == "M": return
            if guess == "H" and isinstance(hints,int) and hints != 0:
                if hints > 0 and len(hints_used) >= hints: continue # Already gotten all our hints
                # Give them a hint
                hints_used = self.get_hint(guesses,target,hints_used)
                continue
            if guess == "CORPNEWT":
                cheat_mode ^= True
                continue
            guess = guess.strip()
            if len(guess) != len(target) or not guess.isalpha():
                self.u.head()
                print("")
                print("Guesses have to be {:,} alphabetical characters.\nNo spaces, numbers, etc.".format(len(target)))
                print("")
                self.u.grab("Press [enter] to continue...")
                continue
            if not guess in self.word_list:
                self.u.head()
                print("")
                print("\"{}\" not found in word list.".format("".join([self.colors[-1].format(x) for x in guess])))
                print("")
                self.u.grab("Press [enter] to continue...")
                continue
            if guess in guesses:
                self.u.head()
                print("")
                print("You have already guessed \"{}\"!".format(guess))
                print("")
                self.u.grab("Press [enter] to continue...")
                continue
            if hard_mode and guesses: # We're in hard mode, and have at least one guess
                rw,rr = self.check_guess(guesses[-1],target)
                if not all((guess[x]==guesses[-1][x] for x in rr)) or not all((guesses[-1][x] in guess for x in rw)):
                    # Missing some we already got - let's build a reply
                    self.u.head()
                    print("")
                    print("Hard mode requires your guesses adhere to the following:\n")
                    if rw:
                        letters = "".join([self.colors[0].format(guesses[-1][x]) for x in rw])
                        print(" - Must contain: {}{}".format("        " if rr else "",letters))
                    if rr:
                        letters = "".join([self.colors[-1].format("?") if x not in rr else self.colors[1].format(guesses[-1][x]) for x in range(len(target))])
                        print(" - Must use the format:  {}".format(letters))
                    print("")
                    self.u.grab("Press [enter] to continue...")
                    continue
            # Got a guess - let's see how close we are
            guesses.append(guess)
            rw,rr = self.check_guess(guess,target)
            if len(rr)==len(target):
                # We got them all right!
                return self.show_win(guesses,target)
            if len(guesses) >= max_guesses:
                # Whoops... we lost :(
                return self.show_lose(guesses,target)

    def show_win(self,guesses,target):
        self.u.head()
        print("")
        print("You WON!")
        print("")
        print("Attempts:\n")
        for i,g in enumerate(guesses,start=1):
            print("{}. {}".format(i,self.pretty_print(g,target)))
        print("")
        self.u.grab("Press [enter] to return to the main menu...")
        return

    def show_lose(self,guesses,target):
        self.u.head()
        print("")
        print("You LOST!")
        print("")
        print("Attempts:\n")
        for i,g in enumerate(guesses,start=1):
            print("{}. {}".format(i,self.pretty_print(g,target)))
        print("")
        print("The correct word was:")
        print("")
        print("   "+self.pretty_print(target,target))
        print("")
        self.u.grab("Press [enter] to return to the main menu...")
        return

    def main(self):
        while True:
            self.u.head()
            print("")
            print("1. New Easy Game   (3 hints, normal mode)")
            print("2. New Normal Game (0 hints, normal mode)")
            print("3. New Hard Game   (0 hints, hard mode)")
            print("")
            print("Q. Quit")
            print("")
            menu = self.u.grab("Please select an option:  ").lower()
            if not menu: continue
            if menu == "q": self.u.custom_quit()
            if menu == "1": self.start_game(hints=3)
            elif menu == "2": self.start_game()
            elif menu == "3": self.start_game(hard_mode=True)

if __name__ == '__main__':
    w = Wordle()
    w.main()