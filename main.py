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
            """,(i,))
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


def add_guest(room_id:str, guest_details:list): # guest_details is going to be a list of tuples 

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
            insert into guests (room_id, name,age,gender,intended_stay,registered_on)
            values
            (?,?,?,?,?,?)
        """,(room_id,*guest))

    con.commit()
    c.print(f"[green] {len(guest_details)} guests added to room {room_id}. [/green]")
   
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

def update_stay(guest_id:str,new_stay):
    cur.execute("""
    update guests
    set intended_stay=?
    where guest_id=?
    """,(new_stay,guest_id))

def update_room_cost(room_id:str,new_cost:str):
    cur.execute("""
    update rooms
    set cost=?
    where room_id=?
    """,(new_cost,room_id))

def check_booked(room_id:str):
    try:
        num_guests=cur.execute("""
        select num_guests from rooms
        where room_id=?
        """,(room_id,)).fetchone()[0]
        if not int(num_guests):
            c.print("[green]This room has not been booked yet[/green]")
        else:
            c.print("[red]This room has already been booked [/red]")
    except KeyError:
        c.print(f"[red]Room {room_id} doesn't exist[/red]")

def search_guest_by_name():
    q = input("Search guest name: ").strip()
    output = cur.execute("select * from guests where name like ?", (f"%{q}%",))
    if not output:
        c.print("[red]No guest with the provided name found![/red]")
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
        8) Calculate profit
        9) Search by guest name
        10) Search by guest ID
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
                all_guest_stats()
            case '4':
                ui_delete_book()
            case '5':
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
if db_was_missing:
    add_data() 
main_menu()

