import sqlite3
import os
import sys
import datetime
from rich.console import Console
from rich.table import Table

db_was_missing = not os.path.exists("./data.db")

con = sqlite3.connect("data.db")
cur = con.cursor()
c=Console()

# Functions
def create_table():
    """
    Creates required tables, namely rooms and guests.
    We kept them in 2 different tables so that we can store multiple guests for the same room.
    """

    cur.execute("""
        create table if not exists
            rooms(
                room_id integer primary key,
                num_guests integer default 0,
                cost integer default 5000 
            )
    """)

    ## Here the intended stay is in Days
    cur.execute("""
    create table if not exists
        guests(
            room_id integer,
            guest_id integer primary key autoincrement,
            name text,
            age integer,
            gender text,
            paid_bill boolean default 0,
            intended_stay integer,
            registered_on DATE,
            foreign key (room_id) references rooms(room_id)
        )
    """)

    if db_was_missing:
        # adding 20 empty rooms
        for i in range(20):
            cur.execute("""
            insert into rooms (room_id, num_guests, cost)
            values
            (?,0,5000)
            """,(i+1,))
        con.commit()


def print_table(data:list,title="Hotel rooms",cols=[]):
    new_data=[]
    for row in data:
        new_data.append(list(map(str,row)))

    table=Table(title=title,style="cyan")

    if(len(cols)==0):
        for col in cur.description:
            table.add_column(col[0])
    else:
        for col in cols:
            table.add_column(col)

    for point in new_data:
        table.add_row(*point)
    c.print(table)



def all_room_stats():
    output = cur.execute("select * from rooms")
    if not output:
        c.print("[red]No rooms present!![/red]")
    print_table(output)

def all_guest_stats():
    output = cur.execute("""
        SELECT 
            g.room_id,g.guest_id,g.name,g.age,g.gender,g.registered_on,g.intended_stay,g.paid_bill,
            r.cost,
            (r.cost * g.intended_stay) AS total_cost
        FROM guests g
        JOIN rooms r
        ON g.room_id = r.room_id
     """)
    if not output:
        c.print("[red]No guests present!![/red]")
    print_table(output,title="Guests")


def add_guest(room_id:str, guest_details:list): 
    cur.execute("""
    select num_guests from rooms
    where room_id=?
    """,(room_id,))

    num_guests=cur.fetchone()[0]

    cur.execute("""
        update rooms
        set num_guests=? 
        where room_id=?
    """,(str(num_guests+len(guest_details)),room_id))

    for guest in guest_details:
        cur.execute("""
            insert into guests (room_id, name,age,gender,paid_bill,intended_stay,registered_on)
            values
            (?,?,?,?,?,?,?)
        """,(room_id,*guest))

    con.commit()
    c.print(f"[green] {len(guest_details)} guest(s) added to room {room_id}. [/green]")
   
def remove_guest(guest_id:str):
    try:
        room_id=cur.execute("select room_id from guests where guest_id=?",(guest_id,)).fetchone()[0]
        cur.execute("""
            update rooms
            set num_guests=num_guests-1
            where room_id=?
        """,(room_id,))

        cur.execute("""
            delete from guests
            where guest_id=?
        """,(guest_id,))

        con.commit()
    except:
        c.print(f"[red] Guest {guest_id} doesn't exist![/red]")

def update_paid(guest_id:str):
    cur.execute("""
    update guests
    set paid_bill=1
    where guest_id=?
    """,(guest_id,))
    con.commit()

def update_stay(guest_id:str,new_stay):
    cur.execute("""
    update guests
    set intended_stay=?
    where guest_id=?
    """,(new_stay,guest_id))
    con.commit()

def update_cost(room_id:str,new_cost:str):
    cur.execute("""
    update rooms
    set cost=?
    where room_id=?
    """,(new_cost,room_id))
    con.commit()

def check_booked(room_id:str):
    num_guests=cur.execute("""
    select num_guests from rooms
    where room_id=?
    """,(room_id,)).fetchone()

    if num_guests==None:
        c.print(f"[red]Room {room_id} doesn't exist[/red]")
        return

    if not num_guests[0]:
        c.print("[green]This room has not been booked yet[/green]")
    else:
        c.print("[red]This room has already been booked [/red]")

def search_guest_by_name():
    q = input("Search guest name: ").strip()
    output = cur.execute("select * from guests where name like ?", (f"%{q}%",))
    if not output:
        c.print("[red]No guest with the provided name found![/red]")
    print_table(output)

def search_guest_by_id():
    ID = input("Enter guest ID: ").strip()
    output = cur.execute("select * from guests where guest_id==?", (ID,))
    if not output:
        c.print("[red]No guest with the provided ID found![/red]")
    print_table(output)

def get_guests(room_id:str):
    cur.execute("""
    select * from guests
    where room_id=?
    """,(room_id,))

    guests=cur.fetchall()
    print_table(guests,title="Guests")

def check_room(room_id:str):
    cur.execute("select * from rooms where room_id=?", (room_id,))
    room= cur.fetchone()
    if not room:
        c.print("[red]Room not found.[/red]")
        return

    table=Table(title="Room record",style="yellow")

    for col in cur.description:
        table.add_column(col[0])

    to_str=list(map(str,room))
    table.add_row(*to_str)
    c.print(table)

    get_guests(room_id)

def remove_guest_ui():
    guest_id=input("Enter guest id:")
    cur.execute("select name from guests where guest_id=?", (guest_id,))
    row = cur.fetchone()
    if not row:
        c.print("[red]No such guest exists![/red]")
        return
    confirm = input(f"Delete '{row[0]}' (id {guest_id})? [y/n]: ").strip().lower()
    if confirm == 'y':
        remove_guest(guest_id)
        c.print("[green]Deleted.[/green]")
    else:
        c.print("[yellow]Aborted.[/yellow]")

def update_paid_ui():
    ID=input("Enter guest ID for guest who paid the bill:")
    update_paid(ID)
    c.print(f"[green]Updated guest {ID} 's status to paid![/green]")

def update_stay_ui():
    ID=input("Enter guest ID:")
    new_stay=input("Enter the new intended stay(in days):")
    update_stay(ID,new_stay)
    c.print(f"[green]Updated guest {ID} 's stay to {new_stay} days!")

def update_cost_ui():
    ID=input("Enter room ID:")
    new_cost=input("Enter new cost for the room:")
    update_cost(ID,new_cost)
    c.print(f"[green]Updated room {ID} 's cost to {new_cost}!")

def check_booked_ui():
    ID=input("Enter room ID:")
    check_booked(ID)

def check_details_ui():
    ID=input("Enter room ID:")
    check_room(ID)

def calculate_profit():
    try:
        total_profit= cur.execute("""
            SELECT 
                SUM(r.cost * g.intended_stay) AS total_profit
            FROM guests g
            JOIN rooms r
            ON g.room_id = r.room_id
         """).fetchone()[0]

        already_paid= cur.execute("""
            SELECT 
                SUM(r.cost * g.intended_stay) AS already_paid
            FROM guests g
            JOIN rooms r
            ON g.room_id = r.room_id
            WHERE g.paid_bill=1
         """).fetchone()[0]
        c.print(f"[blue]Total Profit [/blue] : {total_profit}")
        if already_paid:
            c.print(f"[green]Already Paid [/green] : {already_paid}")
            c.print(f"[red]To Be Paid [/red] : {int(total_profit) - int(already_paid)}")
        else:
            c.print(f"[green]Already Paid [/green] : No one paid yet:(")
            c.print(f"[red]To Be Paid [/red] : {total_profit}")
    except:
        c.print("[red]No guests exist![/red]")


def add_guest_ui():
    room_id=input("Enter the room ID for the new guest:")
    name=input("Name of the guest:")
    age=input("Age of the guest:")
    gender=input("Gender of the guest(M/F):").upper()
    paid_bill=input("Whether they paid bill in advance or not(y/n):").lower()
    intended_stay=input("How many days do they intend to stay? (in days):")

    if name=="" or (not age.isdigit()) or (gender not in ["M","F"]) or (paid_bill not in ["y","n"]) or (not intended_stay.isdigit()):
        c.print("[red]Invalid Data![/red]")
    else:
        paid_bill=True if paid_bill=="y" else False
        add_guest(room_id,[(name,age,gender,paid_bill,intended_stay,datetime.date.today().isoformat())])

def title(s): 
    c.print(f"[bold underline cyan] {s} [/bold underline cyan]")

def pause(msg="[gray]\nPress Enter to continue...[/gray]"):
    c.input(msg)

def main_menu():
    while True:
        c.clear()
        title("Hotel Management System")
        print("""
        1) List all rooms statistics
        2) List all guest statistics
        3) Check details for a particular room
        4) Add guest to a room
        5) Remove a guest from a room
        6) Update bill status
        7) Update stay for a guest
        8) Update cost for a room
        9) Calculate profit
        10) Search by guest name
        11) Search by guest ID
        12) Check if a room is booked
        0) Quit
        """)

        choice = input("Choose an option: ").strip()
        c.clear()
        match choice:
            case '1':
                all_room_stats()
            case '2':
                all_guest_stats()
            case '3':
                check_details_ui()
            case '4':
                add_guest_ui()
            case '5':
                remove_guest_ui()
            case '6':
                update_paid_ui()
            case '7':
                update_stay_ui()
            case '8':
                update_cost_ui()
            case '9':
                calculate_profit()
            case '10':
                search_guest_by_name()
            case '11':
                search_guest_by_id()
            case '12':
                check_booked_ui()
            case '0':
                c.print("[yellow]Bye![/yellow]")
                break
            case _:
                c.print("[red]Invalid choice.[/red]")
        if choice=='0':
            break
        else:
            pause()

create_table()
main_menu()

