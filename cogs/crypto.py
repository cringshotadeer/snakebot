import textwrap

from discord.ext import commands, menus
import discord
import orjson


class CryptoMenu(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=99)

    async def format_page(self, menu, entries):
        return discord.Embed(
            color=discord.Color.blurple(), description=f"```{''.join(entries)}```"
        )


class crypto(commands.Cog):
    """Crypto related commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.DB = bot.DB

    @commands.group(aliases=["coin"])
    async def crypto(self, ctx):
        """Gets some information about crypto currencies."""
        if ctx.invoked_subcommand:
            return

        embed = discord.Embed(colour=discord.Colour.blurple())

        if not ctx.subcommand_passed:
            embed = discord.Embed(color=discord.Color.blurple())
            embed.description = (
                f"```Usage: {ctx.prefix}coin [buy/sell/bal/profile/list/history]"
                f" or {ctx.prefix}coin [token]```"
            )
            return await ctx.send(embed=embed)

        symbol = ctx.subcommand_passed.upper()
        crypto = await self.DB.get_crypto(symbol)

        if not crypto:
            embed.description = f"```Couldn't find {symbol}```"
            return await ctx.send(embed=embed)

        sign = "+" if crypto["change_24h"] >= 0 else ""

        embed.set_author(
            name=f"{crypto['name']} [{symbol}]",
            icon_url=f"https://s2.coinmarketcap.com/static/img/coins/64x64/{crypto['id']}.png",
        )
        embed.description = textwrap.dedent(
            f"""
                ```diff
                Price:
                ${crypto['price']:,.2f}

                Circulating/Max Supply:
                {crypto['circulating_supply']:,}/{crypto['max_supply']:,}

                Market Cap:
                ${crypto['market_cap']:,.2f}

                24h Change:
                {sign}{crypto['change_24h']}%

                24h Volume:
                {crypto['volume_24h']:,.2f}
                ```
            """
        )
        embed.set_image(
            url=f"https://s3.coinmarketcap.com/generated/sparklines/web/1d/usd/{crypto['id']}.png"
        )

        await ctx.send(embed=embed)

    @crypto.command(aliases=["b"])
    async def buy(self, ctx, symbol: str, cash: float):
        """Buys an amount of crypto.

        coin: str
            The symbol of the crypto.
        cash: int
            How much money you want to invest in the coin.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        if cash < 0:
            embed.description = "```You can't buy a negative amount of crypto```"
            return await ctx.send(embed=embed)

        symbol = symbol.upper()
        data = await self.DB.get_crypto(symbol)

        if not data:
            embed.description = f"```Couldn't find crypto {symbol}```"
            return await ctx.send(embed=embed)

        price = float(data["price"])
        member_id = str(ctx.author.id).encode()
        bal = await self.DB.get_bal(member_id)

        if bal < cash:
            embed.description = "```You don't have enough cash```"
            return await ctx.send(embed=embed)

        amount = cash / price

        cryptobal = await self.DB.get_cryptobal(member_id)

        if symbol not in cryptobal:
            cryptobal[symbol] = {"total": 0, "history": [(amount, cash)]}
        else:
            cryptobal[symbol]["history"].append((amount, cash))

        cryptobal[symbol]["total"] += amount
        bal -= cash

        embed = discord.Embed(
            title=f"You bought {amount:.2f} {data['name']}",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Balance: ${bal}")

        await ctx.send(embed=embed)

        await self.DB.put_bal(member_id, bal)
        await self.DB.put_cryptobal(member_id, cryptobal)

    @crypto.command(aliases=["s"])
    async def sell(self, ctx, symbol, amount):
        """Sells crypto.

        symbol: str
            The symbol of the crypto to sell.
        amount: float
            The amount to sell.
        """
        embed = discord.Embed(color=discord.Color.blurple())

        symbol = symbol.upper()
        price = await self.DB.get_crypto(symbol)

        if not price:
            embed.description = f"```Couldn't find {symbol}```"
            return await ctx.send(embed=embed)

        price = price["price"]
        member_id = str(ctx.author.id).encode()
        cryptobal = await self.DB.get_cryptobal(member_id)

        if not cryptobal:
            embed.description = "```You haven't invested.```"
            return await ctx.send(embed=embed)

        if symbol not in cryptobal:
            embed.description = f"```You haven't invested in {symbol}.```"
            return await ctx.send(embed=embed)

        if amount[-1] == "%":
            amount = cryptobal[symbol]["total"] * ((float(amount[:-1])) / 100)
        else:
            amount = float(amount)

        if amount < 0:
            embed.description = "```You can't sell a negative amount of crypto```"
            return await ctx.send(embed=embed)

        if cryptobal[symbol]["total"] < amount:
            embed.description = (
                f"```Not enough {symbol} you have: {cryptobal[symbol]['total']}```"
            )
            return await ctx.send(embed=embed)

        bal = await self.DB.get_bal(member_id)
        cash = amount * float(price)

        cryptobal[symbol]["total"] -= amount

        if cryptobal[symbol]["total"] == 0:
            cryptobal.pop(symbol, None)
        else:
            cryptobal[symbol]["history"].append((-amount, cash))

        bal += cash

        embed.title = f"Sold {amount:.2f} {symbol} for ${cash:.2f}"
        embed.set_footer(text=f"Balance: ${bal}")

        await ctx.send(embed=embed)

        await self.DB.put_bal(member_id, bal)
        await self.DB.put_cryptobal(member_id, cryptobal)

    @crypto.command(aliases=["p"])
    async def profile(self, ctx, member: discord.Member = None):
        """Gets someone's crypto profile.

        member: discord.Member
            The member whos crypto profile will be shown.
        """
        member = member or ctx.author

        member_id = str(member.id).encode()
        cryptobal = await self.DB.get_cryptobal(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not cryptobal:
            embed.description = "```You haven't invested.```"
            return await ctx.send(embed=embed)

        net_value = 0
        msg = (
            f"{member.display_name}'s crypto profile:\n\n"
            " Name:                 Price:             Percent Gain:\n"
        )

        for crypto in cryptobal:
            data = await self.DB.get_crypto(crypto)

            trades = [
                trade[1] / trade[0]
                for trade in cryptobal[crypto]["history"]
                if trade[0] > 0
            ]
            change = ((data["price"] / (sum(trades) / len(trades))) - 1) * 100
            sign = "-" if str(change)[0] == "-" else "+"

            msg += f"{sign} {crypto:>4}: {cryptobal[crypto]['total']:<14.2f}"
            msg += f" Price: ${data['price']:<10.2f} {change:.2f}%\n"

            net_value += cryptobal[crypto]["total"] * float(data["price"])

        embed.description = f"```diff\n{msg}\nNet Value: ${net_value:.2f}```"
        await ctx.send(embed=embed)

    @crypto.command()
    async def bal(self, ctx, symbol: str):
        """Shows how much of a crypto you have.

        symbol: str
            The symbol of the crypto to find.
        """
        symbol = symbol.upper()
        member_id = str(ctx.author.id).encode()

        cryptobal = await self.DB.get_cryptobal(member_id)
        embed = discord.Embed(color=discord.Color.blurple())

        if not cryptobal:
            embed.description = "```You haven't invested.```"
            return await ctx.send(embed=embed)

        if symbol not in cryptobal:
            embed.description = f"```You haven't invested in {symbol}```"
            return await ctx.send(embed=embed)

        crypto = await self.DB.get_crypto(symbol)

        trades = [
            trade[1] / trade[0]
            for trade in cryptobal[symbol]["history"]
            if trade[0] > 0
        ]
        change = ((crypto["price"] / (sum(trades) / len(trades))) - 1) * 100
        sign = "" if str(crypto["change_24h"])[0] == "-" else "+"

        embed.set_author(
            name=f"{crypto['name']} [{symbol}]",
            icon_url=f"https://s2.coinmarketcap.com/static/img/coins/64x64/{crypto['id']}.png",
        )
        embed.description = textwrap.dedent(
            f"""
                ```diff
                Bal: {cryptobal[symbol]['total']}

                Percent Gain/Loss:
                {"" if str(change)[0] == "-" else "+"}{change:.2f}%

                Price:
                ${crypto['price']:,.2f}

                24h Change:
                {sign}{crypto['change_24h']}%
                ```
            """
        )
        embed.set_image(
            url=f"https://s3.coinmarketcap.com/generated/sparklines/web/1d/usd/{crypto['id']}.png"
        )

        await ctx.send(embed=embed)

    @crypto.command()
    async def list(self, ctx):
        """Shows the prices of crypto with pagination."""
        data = []
        for i, (stock, price) in enumerate(self.DB.crypto, start=1):
            price = orjson.loads(price)["price"]

            if not i % 3:
                data.append(f"{stock.decode()}: ${float(price):.2f}\n")
            else:
                data.append(f"{stock.decode()}: ${float(price):.2f}\t".expandtabs())

        pages = menus.MenuPages(
            source=CryptoMenu(data),
            clear_reactions_after=True,
            delete_message_after=True,
        )
        await pages.start(ctx)

    @crypto.command()
    async def history(self, ctx, member: discord.Member = None, amount=10):
        """Gets a members crypto transaction history.

        member: discord.Member
        amount: int
            How many transactions to get
        """
        member = member or ctx.author

        embed = discord.Embed(color=discord.Color.blurple())
        cryptobal = await self.DB.get_cryptobal(str(member.id).encode())

        if not cryptobal:
            embed.description = "```You haven't invested.```"
            return await ctx.send(embed=embed)

        msg = ""

        for crypto in cryptobal:
            msg += f"{crypto}:\n"
            for trade in cryptobal[crypto]["history"]:
                if trade[0] < 0:
                    kind = "Sold"
                else:
                    kind = "Bought"
                msg += f"{kind} {trade[0]:.2f} for ${trade[1]:.2f}\n"
            msg += "\n"

        embed.description = f"```{msg}```"
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Starts crypto cog."""
    bot.add_cog(crypto(bot))
