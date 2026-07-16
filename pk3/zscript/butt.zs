// Slot 2: the Cheeks of Doom, and everything downwind of them.

// The one true ammo. Everything edible in the world converts to this.
class Gas : Ammo
{
	Default
	{
		Inventory.Amount 8;
		Inventory.MaxAmount 100;
		Ammo.BackpackAmount 20;
		Ammo.BackpackMaxAmount 200;
		Inventory.Icon "BEANA0";
		Tag "Gas";
	}
	States
	{
	Spawn:
		TNT1 A -1;
		Stop;
	}
}

// The upgrade. Fills the bottom of the screen, jiggles when you walk.
// Primary: a gas cloud that rips through crowds, leaves a choking cloud where it
//          lands, and blows doors/lifts open on impact.
// Alt: the Thunderclap. Point-blank hot-air blast that hurls everything away,
//      melts whatever is too slow to leave, crop-dusts three clouds, and
//      (optionally) rockets you backwards. Aim at the floor to fart-jump.
class CheeksOfDoom : Weapon
{
	Default
	{
		Weapon.SlotNumber 2;
		Weapon.SelectionOrder 100;
		Weapon.AmmoType "Gas";
		Weapon.AmmoUse 8;
		Weapon.AmmoGive 30;
		Weapon.AmmoType2 "Gas";
		Weapon.AmmoUse2 30;
		Weapon.BobStyle "InverseSmooth";
		Weapon.BobSpeed 1.8;
		Weapon.BobRangeX 0.7;
		Weapon.BobRangeY 0.5;
		Inventory.PickupMessage "You got the CHEEKS OF DOOM! (Slot 2. Alt-fire when surrounded.)";
		Inventory.PickupSound "butt/pickup";
		Obituary "%o was gassed by %k. Silent, but deadly.";
		Tag "Cheeks of Doom";
	}

	States
	{
	Spawn:
		BUPK A 6 Bright;
		BUPK B 6 Bright;
		Loop;
	Ready:
		BUTT A 1
		{
			A_WeaponReady();
			// Idle leakage. Purely cosmetic. Mostly. Toggle: fpb_leaky.
			let cv = CVar.FindCVar('fpb_leaky');
			if ((cv == null || cv.GetInt() != 0) && random[FPBLeak](0, 899) == 0)
				A_StartSound("butt/leak", CHAN_7, 0, 0.35);
		}
		Loop;
	Deselect:
		BUTT A 1 A_Lower(14);
		Loop;
	Select:
		BUTT A 1 A_Raise(14);
		Loop;
	Fire:
		BUTT B 4;
		BUTT C 3 Bright
		{
			A_StartSound("butt/fart", CHAN_WEAPON);
			A_FireProjectile("GasCloud", frandom[FPBFart](-2, 2), true, 0, -14);
			FPB_GoreHandler.Bump('farts');
			A_AlertMonsters();
			A_Quake(1, 4, 0, 128);
			let cv = CVar.FindCVar('fpb_fartjump');
			if (cv && cv.GetInt() != 0) A_Recoil(1.5);
		}
		BUTT D 3 Bright;
		BUTT B 4;
		BUTT A 5 A_ReFire;
		Goto Ready;
	AltFire:
		BUTT B 5 A_StartSound("butt/inhale", CHAN_WEAPON);
		BUTT B 10;
		BUTT C 4 Bright A_MegaFart;
		BUTT D 6 Bright;
		BUTT B 8;
		BUTT A 10;
		Goto Ready;
	}

	action void A_MegaFart()
	{
		if (player == null) return;
		invoker.DepleteAmmo(invoker.bAltFire, true);

		A_StartSound("butt/mega", CHAN_WEAPON);
		FPB_GoreHandler.Bump('farts');
		A_AlertMonsters();
		A_Quake(4, 18, 0, 512);

		// Hot air: hurl everything nearby away from you (bosses hold their ground).
		A_Blast(0, 255, 300, 24, "GasBlastFX", "");

		// Acid bath: melt whatever stayed in the splash zone.
		BlockThingsIterator it = BlockThingsIterator.Create(self, 280);
		while (it.Next())
		{
			let mo = it.thing;
			if (mo == null || mo == self) continue;
			if (!mo.bShootable || mo.health <= 0) continue;
			if (mo.player) continue;               // immune to your own brand
			double dist = Distance3D(mo);
			if (dist > 280) continue;
			if (!CheckSight(mo)) continue;
			int dmg = int(95 * (1.0 - dist / 300.0));
			if (dmg > 0) mo.DamageMobj(self, self, dmg, 'FartAcid', DMG_THRUSTLESS);
		}

		// Crop-dust the fairway.
		A_FireProjectile("GasCloud", -12, false, 0, -14);
		A_FireProjectile("GasCloud",   0, false, 0, -14);
		A_FireProjectile("GasCloud",  12, false, 0, -14);

		// Newton's third law of thunder. Aim at the floor to launch yourself.
		let cv = CVar.FindCVar('fpb_fartjump');
		if (cv && cv.GetInt() != 0)
		{
			double p = pitch;
			vel = (
				vel.x - cos(angle) * cos(p) * 9,
				vel.y - sin(angle) * cos(p) * 9,
				vel.z + sin(p) * 11 + 2
			);
		}
	}
}

// The traveling puff. Rips through enemies, splats on walls, and tries to
// "blow the door down" when it hits a line with a door/lift special.
class GasCloud : Actor
{
	Default
	{
		Projectile;
		+RIPPER
		+FORCEXYBILLBOARD
		Radius 12;
		Height 14;
		Speed 16;
		Damage 4;              // Doom missile rule: 4 x 1d8 per rip
		DamageType 'FartGas';
		ReactionTime 22;       // flight time cap; then it settles into a cloud
		RenderStyle "Translucent";
		Alpha 0.8;
		Scale 0.9;
		Decal "FartSplat";
		Obituary "%o was crop-dusted by %k.";
	}

	States
	{
	Spawn:
		FART A 3 Bright A_Countdown;
		FART B 3 Bright A_Countdown;
		FART C 3 Bright A_Countdown;
		Loop;
	Death:
		TNT1 A 0
		{
			TryBlowDoor();
			let pc = Spawn("StinkCloud", pos);
			if (pc) pc.target = target;    // credit the farter for cloud kills
		}
		FART C 3 Bright A_FadeOut(0.2);
		Wait;
	}

	// "Blows through walls": any door or lift the puff slams into gets activated,
	// as if used. Locked doors still check the farter's keys. Toggle: fpb_doorfarts.
	void TryBlowDoor()
	{
		let cv = CVar.FindCVar('fpb_doorfarts');
		if (cv && cv.GetInt() == 0) return;
		let l = BlockingLine;
		if (l == null || l.special == 0 || target == null) return;

		switch (l.special)
		{
		case 10: case 11: case 12: case 13: case 14:   // Door_Close/Open/Raise/LockedRaise/Animated
		case 202:                                       // Generic_Door
		case 62: case 64: case 66: case 67: case 68:    // Plat_* lifts
		case 203: case 206:                             // Generic_Lift, Plat_DownWaitUpStayLip
			level.ExecuteSpecial(l.special, target, l, false,
				l.args[0], l.args[1], l.args[2], l.args[3], l.args[4]);
			FPB_GoreHandler.Bump('doors');
			break;
		default:
			break;
		}
	}
}

// The lingering stink. Grows, chokes everything inside (pain-lock = coughing),
// then thins out. Suffocation deaths are handled by the gore event handler.
class StinkCloud : Actor
{
	int puffs;

	Default
	{
		+NOBLOCKMAP
		+NOGRAVITY
		+NOCLIP
		+NOTELEPORT
		+FORCEXYBILLBOARD
		Radius 2;
		Height 4;
		RenderStyle "Translucent";
		Alpha 0.55;
		Scale 0.7;
		Obituary "%o inhaled %k's essence.";
	}

	States
	{
	Spawn:
		PGAS A 0 NoDelay A_StartSound("gas/hiss", CHAN_BODY, CHANF_LOOPING, 0.45, ATTN_IDLE);
	Waft:
		PGAS A 5 Bright A_GasWork;
		PGAS B 5 Bright A_GasWork;
		PGAS C 5 Bright A_GasWork;
		PGAS D 5 Bright A_GasWork;
		Loop;
	Fade:
		TNT1 A 0 A_StopSound(CHAN_BODY);
		PGAS D 3 A_FadeOut(0.035);
		Wait;
	}

	void A_GasWork()
	{
		scale = (min(1.7, scale.x + 0.045), min(1.7, scale.y + 0.045));
		puffs++;
		if (puffs >= 36)
		{
			SetStateLabel("Fade");
			return;
		}
		if ((puffs % 2) == 0) return;   // damage tick every other frame

		let src = target;
		BlockThingsIterator it = BlockThingsIterator.Create(self, 150);
		while (it.Next())
		{
			let mo = it.thing;
			if (mo == null || mo == src) continue;
			if (!mo.bShootable || mo.health <= 0) continue;
			if (mo.player) continue;
			if (Distance3D(mo) > 150) continue;
			mo.DamageMobj(self, src, 3, 'FartGas', DMG_THRUSTLESS);
			if (random[FPBGas](0, 255) < 24)
				mo.A_StartSound("butt/choke", CHAN_VOICE, 0, 0.8);
		}
	}
}

// Visual ring for the Thunderclap blast.
class GasBlastFX : Actor
{
	Default
	{
		+NOBLOCKMAP
		+NOGRAVITY
		+NOINTERACTION
		+FORCEXYBILLBOARD
		RenderStyle "Add";
		Alpha 0.7;
		Scale 0.6;
	}
	States
	{
	Spawn:
		FBLS A 3 Bright;
		FBLS B 3 Bright;
		FBLS C 3 Bright A_FadeOut(0.18);
		Wait;
	}
}
