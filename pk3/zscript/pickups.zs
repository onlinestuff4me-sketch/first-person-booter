// World replacements. Every gun spot in every map becomes the butt upgrade
// (owning it already? the duplicate tops up your gas), and every ammo pickup
// becomes something regrettable to eat. Health, armor and keys stay vanilla.

// Weapon spots -> Cheeks of Doom.
class Cheeks1 : CheeksOfDoom replaces Shotgun {}
class Cheeks2 : CheeksOfDoom replaces SuperShotgun {}
class Cheeks3 : CheeksOfDoom replaces Chaingun {}
class Cheeks4 : CheeksOfDoom replaces RocketLauncher {}
class Cheeks5 : CheeksOfDoom replaces PlasmaRifle {}
class Cheeks6 : CheeksOfDoom replaces BFG9000 {}
class Cheeks7 : CheeksOfDoom replaces Chainsaw {}

// Small ammo -> a modest can of beans. (Zombies drop these now.)
class Beans : Gas replaces Clip
{
	Default
	{
		Inventory.Amount 10;
		Inventory.PickupMessage "Beans. The magical fruit.";
		Tag "Beans";
	}
	States
	{
	Spawn:
		BEAN A -1;
		Stop;
	}
}
class Beans2 : Beans replaces Shell {}
class Beans3 : Beans replaces RocketAmmo {}

// Big ammo -> five-alarm chili.
class ChiliPot : Gas replaces Cell
{
	Default
	{
		Inventory.Amount 25;
		Inventory.PickupMessage "Five-alarm chili. Handle with care.";
		Tag "Chili Pot";
	}
	States
	{
	Spawn:
		CHLI A -1;
		Stop;
	}
}
class ChiliPot2 : ChiliPot replaces ClipBox {}
class ChiliPot3 : ChiliPot replaces ShellBox {}
class ChiliPot4 : ChiliPot replaces RocketBox {}

class ChiliCauldron : ChiliPot replaces CellPack
{
	Default
	{
		Inventory.Amount 60;
		Inventory.PickupMessage "The Cauldron of Regret. Gas +60.";
		Tag "Chili Cauldron";
		Scale 1.4;
	}
}

// Berserk -> the forbidden snack. Full heal, full tank, cheeks out.
class GasStationSushi : CustomInventory replaces Berserk
{
	Default
	{
		Inventory.PickupMessage "GAS-STATION SUSHI! Health restored. Tank... very full.";
		Inventory.PickupSound "butt/pickup";
	}
	States
	{
	Spawn:
		MBNS A 6 Bright;
		MBNS B 6 Bright;
		Loop;
	Pickup:
		TNT1 A 0
		{
			A_GiveInventory("Gas", 200);
			HealThing(100, 0);
			A_SelectWeapon("CheeksOfDoom");
		}
		Stop;
	}
}
