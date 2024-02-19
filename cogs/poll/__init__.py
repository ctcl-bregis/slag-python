# SLAG - CTCL 2024
# File: cogs/poll/__init__.py
# Purpose: User polls extension
# Created: February 18, 2024
# Modified: February 18, 2024



def setup(client):
    client.add_cog(Poll(client))