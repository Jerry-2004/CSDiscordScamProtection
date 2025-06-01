from db import remove_guild_from_whitelist

def main():
    guild_id = input("Enter the guild ID to remove from whitelist: ").strip()
    if not guild_id.isdigit():
        print("Invalid guild ID. Must be a number.")
        return

    remove_guild_from_whitelist(int(guild_id))
    print(f"✅ Guild {guild_id} removed from whitelist.")

if __name__ == "__main__":
    main()