import sys
from shell import FileManagerShell

def main() -> None:
    app = FileManagerShell()
    try:
        app.cmdloop()
    except KeyboardInterrupt:
        print("\nЗавершение работы.")
        sys.exit(0)

if __name__ == '__main__':
    main()