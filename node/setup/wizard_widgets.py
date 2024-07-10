
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm

def get_int(prompt: str, default: int | None = None) -> int:
    '''
    Get an integer from a prompt
    
    Args:
        prompt (str): Prompt message
        default (int | None): Default option, or none for required input
    Returns:
        int: Recorded input integer
    '''

    return int(IntPrompt.ask(prompt, default=default))

def get_string(prompt: str, default: str | None = None) -> str:
    '''
    Get a string from a prompt
    
    Args:
        prompt (str): Prompt message
        default (str | None): Default option, or none for required input
    Returns:
        str: Recorded input
    '''

    return str(Prompt.ask(prompt, default=default))

def get_yes_no(prompt: str, default: bool = True) -> bool:
    '''
    Get a True/False from a prompt with the ability to set a default value
    
    Args:
        prompt (str): Prompt message
        default (bool): Default result (true by default)
    Returns:
        bool: Result status
    '''

    return Confirm.ask(prompt, default=default)

def get_password(prompt: str) -> str:
    '''
    Get a string in a protected form (we feelin fancy n shi, getpass aint good enough)

    Args:
        prompt (str): Prompt message
    Returns:
        str: Password string
    '''
    
    # This is junky, but it's only used one so idc
    import sys

    if sys.platform.startswith('win'): 
        from getpass import getpass
        return getpass(prompt)

    import termios, tty

    def get_char():
        fd = sys.stdin.fileno()
        
        # TODO: Dont keep resetting settings every character ffs

        # Keep the previous terminal settings so we dont fuck shit up
        settings = termios.tcgetattr(fd)

        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)

        termios.tcsetattr(fd, termios.TCSADRAIN, settings)

        return ch

    con = Console()

    con.print(prompt, end = '')

    password: str = ''
    
    while True:
        ch = get_char()

        if ch == '\n' or ch == '\r': break
        elif ch == '\x7f': # BSPC
            if len(password) <= 0: continue

            password = password[:-1]
            con.print('\b', end = '', style = 'bold green')
            sys.stdout.flush()

        else:
            password += ch
            con.print('*', end = '', style = 'bold green')
            sys.stdout.flush()

    con.print()
    return password

def get_password_and_verify(prompt: str) -> str | None:
    '''
    Get a password and verify it by asking for the user to retype

    Returns:
        str | None: Resulting password string, or none is not password is entered. Your life your choices
    '''
    con = Console()

    password = get_password(prompt)

    repass = get_password('Re-Type the password: ')

    if repass != password:
        con.print('You failed to retype the password.', style = 'bold red')
        return None

    return password



