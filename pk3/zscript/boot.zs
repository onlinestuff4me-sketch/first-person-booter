// Slot 1: The Boot. No ammo, no mercy.
// Primary: kick. Anything the kick kills is guaranteed to burst (extreme death + giblet shower).
// Alt: wind-up punt. Slower, triple thrust — field-goal an imp across the room.
class Boot : Weapon
{
	Default
	{
		Weapon.SlotNumber 1;
		Weapon.SelectionOrder 3000;
		Weapon.Kickback 100;
		Weapon.BobStyle "Smooth";
		Weapon.BobSpeed 2.0;
		+WEAPON.MELEEWEAPON
		Obituary "%o was punted into giblets by %k's size-40 boot.";
		Tag "The Boot";
		Inventory.PickupMessage "The Boot. It was on you all along.";
	}

	States
	{
	Spawn:
		TNT1 A -1;
		Stop;
	Ready:
		BOOT A 1 A_WeaponReady;
		Loop;
	Deselect:
		BOOT A 1 A_Lower(18);
		Loop;
	Select:
		BOOT A 1 A_Raise(18);
		Loop;
	Fire:
		BOOT B 3;
		BOOT C 2 A_StartSound("boot/whoosh", CHAN_WEAPON);
		BOOT D 3 A_BootKick(1.0);
		BOOT C 4;
		BOOT B 4;
		BOOT A 5;
		Goto Ready;
	AltFire:
		BOOT B 6 A_StartSound("boot/whoosh", CHAN_WEAPON, 0, 0.7, ATTN_NORM, 0.55);
		BOOT B 9;
		BOOT C 2 A_StartSound("boot/whoosh", CHAN_WEAPON, 0, 1.0, ATTN_NORM, 0.85);
		BOOT D 3 A_BootKick(2.6);
		BOOT C 5;
		BOOT B 5;
		BOOT A 8;
		Goto Ready;
	}

	// power scales damage and punt force. The gib guarantee is the whole point:
	// if the kick is lethal, damage is raised past the target's gib threshold so
	// the engine plays its extreme death, and the gore handler adds the confetti.
	action void A_BootKick(double power)
	{
		if (player == null) return;

		double range = 84;
		double ang = angle;
		FTranslatedLineTarget scan;
		double aimPitch = AimLineAttack(ang, range, scan, 0., ALF_CHECK3D);

		int dmg = int(140 * power);
		let mark = scan.linetarget;
		if (mark && mark.bShootable && dmg >= mark.health)
		{
			dmg = max(dmg, mark.health + abs(mark.GetGibHealth()) + 5);
		}

		FTranslatedLineTarget t;
		LineAttack(ang, range, aimPitch, dmg, 'Kick', "BootPuff", LAF_ISMELEEATTACK, t);

		let victim = t.linetarget;
		if (victim)
		{
			A_StartSound("boot/splat", CHAN_AUTO);
			A_Quake(2, 6, 0, 256);
			if (!victim.bDontThrust)
			{
				double push = 20.0 * power * 100.0 / max(50, victim.mass);
				push = min(push, 45);
				victim.vel = (
					victim.vel.x + cos(ang) * push,
					victim.vel.y + sin(ang) * push,
					victim.vel.z + push * 0.4
				);
				// a demon in flight is a bowling ball with feelings
				if (victim.bIsMonster)
				{
					let w = FPB_BowlingWatcher(
						Spawn("FPB_BowlingWatcher", victim.pos));
					if (w)
					{
						w.tracer = victim;
						w.target = self;
					}
				}
			}
		}
		else
		{
			// Kicked nothing living. Corpses to tidy? Sports equipment?
			Actor corpse = null;
			FPB_Eyeball ball = null;
			BlockThingsIterator it = BlockThingsIterator.Create(self, 96);
			while (it.Next())
			{
				let mo = it.thing;
				if (mo == null) continue;
				double dist = Distance2D(mo);
				if (dist > 80) continue;
				if (dist > 24 && AbsAngle(ang, AngleTo(mo)) > 50) continue;
				if (corpse == null && mo.bCorpse && mo.bIsMonster)
					corpse = mo;
				if (ball == null) ball = FPB_Eyeball(mo);
			}
			if (corpse)
			{
				// re-gib the fallen: rude to them, devastating to Arch-viles
				A_StartSound("boot/splat", CHAN_AUTO);
				A_Quake(1, 4, 0, 128);
				FPB_GoreHandler.BurstIntoGiblets(corpse);
				FPB_GoreHandler.Bump('tidied');
				corpse.Destroy();
			}
			else if (ball)
			{
				ball.vel = (cos(ang) * 18 * power, sin(ang) * 18 * power,
					7 + 3 * power);
				ball.A_StartSound("gore/eyesqueak", CHAN_BODY);
				FPB_GoreHandler.Bump('eyepunts');
			}
		}
	}
}

// The FULL COMPOST reward: fifteen golden seconds of double boot damage.
// Granted by the gore handler when you land five kick-kills in four seconds.
class FPB_GoldenLeg : PowerDamage
{
	Default
	{
		Powerup.Duration -15;
		Powerup.Color "Gold", 0.15;
		DamageFactor 2;
	}
}

// Impact flash for the kick. SeeSound doubles as the wall-thud.
class BootPuff : Actor
{
	Default
	{
		+NOBLOCKMAP
		+NOGRAVITY
		+PUFFONACTORS
		+FORCEXYBILLBOARD
		RenderStyle "Add";
		Alpha 0.9;
		SeeSound "boot/thud";
	}
	States
	{
	Spawn:
		KPUF A 3 Bright;
		KPUF B 3 Bright;
		Stop;
	}
}
