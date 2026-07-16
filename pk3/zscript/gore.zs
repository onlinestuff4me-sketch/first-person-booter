// Death flavor, applied from the outside so it works on ANY monster set
// (Freedoom, Doom, other mods) without touching their classes:
//   Kick     -> extra giblet shower on top of the engine's extreme death
//   FartGas  -> victim keels over green (suffocated)
//   FartAcid -> corpse squashes into a bubbling goo pile (melted)
// Also the town crier: level-start tips and per-map gib milestones.
class FPB_GoreHandler : EventHandler
{
	int kickGibs;

	static const String kTips[] = {
		"Kick barrels. Trust the process.",
		"Farts open doors. Knocking is for cowards.",
		"Aim at the floor and alt-fire to attempt flight.",
		"The gas cloud lingers. So does the shame.",
		"Melted demons cannot be resurrected. Arch-viles hate this one trick.",
		"Duplicate cheeks convert directly into gas. That's just science.",
		"A punted imp flies farther than a thrown one.",
		"Your own brand cannot hurt you. Others are less fortunate.",
		"Beans are the magical fruit. The legends were true.",
		"Bosses are too heavy to blow away. Marinate them instead.",
		"Stepping on an eyeball is considered good luck. By us.",
		"Gas-station sushi restores health. Do not question this.",
		"Try 'fpb_gore 4' in the console. You didn't hear it from us.",
		"The whole map hears every fart. This is by design. Yours."
	};

	static const int kMilestones[] = { 5, 15, 30, 60, 100, 200 };
	static const String kTitles[] = {
		"FIVE GIBS: THE LEG IS AWAKE.",
		"FIFTEEN GIBS: CERTIFIED PODIATRIST OF PAIN.",
		"THIRTY GIBS: HELL HAS FILED A COMPLAINT.",
		"SIXTY GIBS: LEG DAY IS EVERY DAY.",
		"ONE HUNDRED GIBS: THE BOOT REMEMBERS.",
		"TWO HUNDRED GIBS: JANITORS OF HELL, UNIONIZE."
	};

	override void WorldLoaded(WorldEvent e)
	{
		if (e.IsSaveGame) return;
		Console.Printf("\c[Gold]TIP:\c- %s",
			kTips[random[FPBTip](0, kTips.Size() - 1)]);
	}

	override void WorldThingDied(WorldEvent e)
	{
		let mo = e.Thing;
		if (mo == null || mo.player != null || !mo.bIsMonster) return;

		Name dt = mo.DamageTypeReceived;
		if (dt == 'Kick')
		{
			BurstIntoGiblets(mo);
			kickGibs++;
			for (int i = 0; i < kMilestones.Size(); i++)
			{
				if (kickGibs == kMilestones[i])
				{
					Console.Printf("\c[Red]%s\c-", kTitles[i]);
					break;
				}
			}
		}
		else if (dt == 'FartGas')
		{
			mo.A_SetTranslation('PoisonSkin');
			mo.A_StartSound("butt/choke", CHAN_VOICE);
		}
		else if (dt == 'FartAcid')
		{
			let m = AcidMelter(Actor.Spawn("AcidMelter", mo.pos));
			if (m) m.tracer = mo;
		}
	}

	static void BurstIntoGiblets(Actor mo)
	{
		int mult = 3;
		let cv = CVar.FindCVar('fpb_gore');
		if (cv) mult = clamp(cv.GetInt(), 0, 4);
		if (mult <= 0) return;

		mo.A_StartSound("boot/gib", CHAN_AUTO);

		// the puddle forms where they used to be
		let pool = Actor.Spawn("FPB_BloodPool",
			(mo.pos.x, mo.pos.y, mo.floorz));
		if (pool)
		{
			double ps = clamp(mo.radius / 40.0, 0.35, 0.9);
			pool.scale = (ps, ps);
		}

		int n = (4 + random[FPBGore](0, 4)) * mult;
		for (int i = 0; i < n; i++)
		{
			// ~1 in 6 chunks still has gas in it. Gastrointestinal aftershocks.
			String cls = (random[FPBGore](0, 5) == 0) ? "FPB_PopChunk"
			                                          : "MeatChunk";
			let chunk = Actor.Spawn(cls, mo.pos + (0, 0, max(8, mo.height * 0.5)));
			if (chunk == null) continue;
			chunk.vel = (
				random[FPBGore](-100, 100) / 16.0,
				random[FPBGore](-100, 100) / 16.0,
				random[FPBGore](30, 110) / 14.0
			);
			double s = 0.6 + random[FPBGore](0, 70) / 100.0;
			chunk.scale = (s, s);
		}

		// most demons have at least one eye to lose
		if (random[FPBGore](0, 99) < 60)
		{
			let eye = Actor.Spawn("FPB_Eyeball",
				mo.pos + (0, 0, max(8, mo.height * 0.5)));
			if (eye)
			{
				eye.vel = (
					random[FPBGore](-60, 60) / 16.0,
					random[FPBGore](-60, 60) / 16.0,
					random[FPBGore](40, 90) / 14.0
				);
			}
		}
	}
}

// A flying piece of former demon. Tumbles, bounces wetly, settles as a splat,
// and smears the walls on the way through.
class MeatChunk : Actor
{
	Default
	{
		Projectile;
		-NOGRAVITY
		-ACTIVATEIMPACT
		-ACTIVATEPCROSS
		+THRUACTORS
		+FORCEXYBILLBOARD
		+NOTELEPORT
		Radius 5;
		Height 6;
		Gravity 0.7;
		Damage 0;
		BounceType "Doom";
		BounceFactor 0.5;
		WallBounceFactor 0.6;
		BounceCount 4;
		BounceSound "gore/bounce";
		Decal "BloodSplat";
	}
	States
	{
	Spawn:
		GIBS A 3;
		GIBS B 3;
		GIBS C 3;
		GIBS D 3;
		Loop;
	Death:
		GIBS E 300;
		GIBS E 2 A_FadeOut(0.04);
		Wait;
	}
}

// The chunk that wasn't done digesting. Pops with a tiny toot and a bit of
// splash damage — yes, it can catch you too. Stand back from your fireworks.
class FPB_PopChunk : MeatChunk
{
	Default
	{
		BounceCount 2;
	}
	States
	{
	Death:
		TNT1 A 0 A_StartSound("butt/pop", CHAN_BODY, 0, 0.8);
		TNT1 A 0 A_Explode(5, 60);
		FART B 3 Bright;
		FART C 3 Bright A_FadeOut(0.3);
		Wait;
	}
}

// The puddle that forms under a proper gibbing. Spreads, sits, soaks in.
class FPB_BloodPool : Actor
{
	Default
	{
		+NOBLOCKMAP
		+NOGRAVITY
		+FLATSPRITE
		Radius 16;
		Height 2;
		RenderStyle "Translucent";
		Alpha 0.9;
		Scale 0.4;
	}
	States
	{
	Grow:
	Spawn:
		BPOL A 3
		{
			A_SetScale(min(1.5, scale.x + 0.09));
			if (scale.x >= 1.5) SetStateLabel("Rest");
		}
		Loop;
	Rest:
		BPOL B 500;
		BPOL C 350;
	Fade:
		BPOL C 3 A_FadeOut(0.02);
		Wait;
	}
}

// It rolls free, it comes to rest, it stares. Walk over it to squish it.
class FPB_Eyeball : CustomInventory
{
	Default
	{
		Radius 6;
		Height 8;
		+DROPOFF
		Scale 0.9;
	}

	static const String kSquish[] = {
		"You stepped on an eye. It was watching.",
		"Squish.",
		"Ew. Ew ew ew.",
		"That popped more than you expected.",
		"Free eyeball. Don't think about where it's been.",
		"Waste not. Squish lots."
	};

	override String PickupMessage()
	{
		return kSquish[random[FPBEye](0, kSquish.Size() - 1)];
	}

	States
	{
	Spawn:
		EYEB A 320;
	Fade:
		EYEB A 2 A_FadeOut(0.04);
		Wait;
	Pickup:
		TNT1 A 0 A_StartSound("gore/bounce", CHAN_AUTO, 0, 0.9);
		Stop;
	}
}

// Invisible worker that squashes an acid-killed corpse into the floor,
// then swaps it for goo. Melted demons cannot be resurrected. Tragic.
class AcidMelter : Actor
{
	int timer;

	Default
	{
		+NOINTERACTION
		+NOBLOCKMAP
		+NOGRAVITY
	}
	States
	{
	Spawn:
		TNT1 A -1;
		Stop;
	}

	override void Tick()
	{
		Super.Tick();
		let c = tracer;
		if (c == null)
		{
			Destroy();
			return;
		}
		if (timer == 0)
		{
			c.A_SetTranslation('AcidGoo');
			c.A_StartSound("goo/melt", CHAN_BODY);
		}
		c.scale = (c.scale.x * 1.015, c.scale.y * 0.90);
		timer++;
		if (timer >= 28)
		{
			double s = max(0.8, c.radius / 20.0);
			let goo = Actor.Spawn("GooPile", c.pos);
			if (goo) goo.scale = (s, s);
			c.Destroy();
			Destroy();
		}
	}
}

// What's left after the acid option. Bubbles apologetically, then evaporates.
class GooPile : Actor
{
	int life;

	Default
	{
		+NOBLOCKMAP
		+NOGRAVITY
		+FLATSPRITE
		Radius 12;
		Height 2;
		RenderStyle "Translucent";
		Alpha 0.85;
	}
	States
	{
	Spawn:
		GOOP A 8
		{
			if (random[FPBGoo](0, 255) < 48)
				A_StartSound("goo/bubble", CHAN_BODY, 0, 0.5);
		}
		GOOP B 8;
		GOOP C 8
		{
			life++;
			if (life > 14) SetStateLabel("Fade");
		}
		Loop;
	Fade:
		GOOP C 3 A_FadeOut(0.03);
		Wait;
	}
}
