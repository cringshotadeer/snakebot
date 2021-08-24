import unittest
import asyncio

from aiohttp import ClientSession

from bot import Bot
from tests.helpers import MockBot, MockContext, MockMessage
from cogs.animals import animals
from cogs.misc import misc
from cogs.useful import useful
from cogs.stocks import stocks
from cogs.crypto import crypto

bot = Bot(MockBot())
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class AdminCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class AnimalsCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = animals(bot=bot)

    async def test_cat_commands(self):
        if not bot.client_session:
            bot.client_session = ClientSession()

        context = MockContext()

        for command in ("cat", "cat2", "cat3", "cat4"):
            with self.subTest(command=command):

                await getattr(self.cog, command)(self.cog, context)

                self.assertEqual(
                    context.send.call_args.args[0][:4],
                    "http",
                )


class ApisCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class Background_TasksCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class CryptoCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = crypto(bot=bot)

    async def test_crypto_command(self):
        context = MockContext()
        context.invoked_subcommand = None
        context.subcommand_passed = "BTC"

        await self.cog.crypto(self.cog, context)

        self.assertNotEqual(
            context.send.call_args.kwargs["embed"].description,
            "```No stock found for BTC```",
        )


class EconomyCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class EventsCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class HelpCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class InformationCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class MiscCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = misc(bot=bot)

    async def test_yeah_command(self):
        context = MockContext()

        await self.cog.yeah(self.cog, context)

        context.send.assert_called_with("Oh yeah its all coming together")

    async def test_convert_command(self):
        context = MockContext()

        await self.cog.convert(self.cog, context, number=32)

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            "```32°F is 0.00°C```",
        )

    async def test_ones_command(self):
        context = MockContext()

        await self.cog.ones(self.cog, context, number=32)

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            "```011111```",
        )

    async def test_twos_command(self):
        context = MockContext()

        await self.cog.twos(self.cog, context, number=32, bits=8)

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            "```00100000```",
        )

    async def test_nato_command(self):
        context = MockContext()

        await self.cog.nato(
            self.cog, context, text="the quick brown fox jumps over 13 lazy dogs"
        )

        context.send.assert_called_with(
            "Tango Hotel Echo (space) Quebec Uniform India Charlie Kilo (space) Bravo "
            "Romeo Oscar Whiskey November (space) Foxtrot Oscar X-ray (space) Juliett "
            "Uniform Mike Papa Sierra (space) Oscar Victor Echo Romeo (space) One Three"
            " (space) Lima Alfa Zulu Yankee (space) Delta Oscar Golf Sierra ",
        )

    async def test_embedjson_command(self):
        context = MockContext()

        await self.cog.embed_json(self.cog, context, message=MockMessage())

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description[:61],
            '```json\n<MagicMock name="mock.embeds.__getitem__().to_dict()"',
        )


class ModerationCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class MusicCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class OwnerCogTests(unittest.IsolatedAsyncioTestCase):
    pass


class StocksCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = stocks(bot=bot)

    async def test_stock_command(self):
        context = MockContext()
        context.invoked_subcommand = None
        context.subcommand_passed = "TSLA"

        await self.cog.stock(self.cog, context)

        self.assertNotEqual(
            context.send.call_args.kwargs["embed"].description,
            "```No stock found for TSLA```",
        )


class UsefulCogTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cog = useful(bot=bot)

    async def test_calc_command(self):
        context = MockContext()

        await self.cog.calc(self.cog, context, num_base="hex", args="0x7d * 0x7d")

        self.assertEqual(
            context.send.call_args.kwargs["embed"].description,
            "```ml\n125 * 125\n\n3d09\n\nDecimal: 15625```",
        )
