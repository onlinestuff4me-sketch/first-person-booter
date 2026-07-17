// Death flavor, applied from the outside so it works on ANY monster set
// (Freedoom, Doom, other mods) without touching their classes:
//   Kick     -> extra giblet shower on top of the engine's extreme death
//   FartGas  -> victim keels over green (suffocated)
//   FartAcid -> corpse squashes into a bubbling goo pile (melted)
// Also the town crier (tips, milestones), the accountant (level stats),
// and the windshield (screen gunk on point-blank gibs).
class FPB_GoreHandler : EventHandler
{
	// per-map ledger
	int kickGibs;
	int gasKills;
	int melts;
	int doors;
	int farts;
	int eyes;
	int bowled;
	int eyepunts;
	int tidied;
	int lastQuipTic;
	Array<int> kickTics;

	// screen gunk slots (written in play, read in RenderOverlay)
	int gunkBorn[8];
	double gunkX[8];
	double gunkY[8];
	double gunkS[8];
	int gunkT[8];

	static const String kTips[] = {
		"Kick barrels. Trust the process.",
		"Farts open doors. Knocking is for cowards.",
		"Aim at the floor and alt-fire to attempt flight.",
		"The gas cloud lingers. So does the shame.",
		"Melted demons cannot be resurrected. Arch-viles hate this one trick.",
		"Duplicate cheeks convert directly into gas. That's just science.",
		"A punted imp can knock over his friends. Aim for the group photo.",
		"Your own brand cannot hurt you. Others are less fortunate.",
		"Beans are the magical fruit. The legends were true.",
		"Bosses are too heavy to blow away. Marinate them instead.",
		"Stepping on an eyeball is considered good luck. By us.",
		"Gas-station sushi restores health. Do not question this.",
		"Try 'fpb_gore 4' in the console. You didn't hear it from us.",
		"Type 'netevent fpb_stats' in the console for your running tally.",
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

	static const String kQuips[] = {
		"MOIST.",
		"THAT ONE HAD PLANS.",
		"CLEANUP ON AISLE EVERYWHERE.",
		"THE FLOOR IS SOUP NOW.",
		"PROFESSIONAL.",
		"SOMEWHERE, A MOP WEEPS."
	};

	// Other classes report their deeds here.
	static void Bump(Name what, int amount = 1)
	{
		let h = FPB_GoreHandler(EventHandler.Find("FPB_GoreHandler"));
		if (h == null) return;
		if (what == 'doors') h.doors += amount;
		else if (what == 'farts') h.farts += amount;
		else if (what == 'eyes') h.eyes += amount;
		else if (what == 'bowled') h.bowled += amount;
		else if (what == 'eyepunts') h.eyepunts += amount;
		else if (what == 'tidied') h.tidied += amount;
	}

	String BuildCard()
	{
		return String.Format(
			"\c[Gold]=== LEVEL DIGESTED ===\c-\n"
			"Boots applied: %d    Corpses tidied: %d\n"
			"Farts fired: %d    Doors blown open: %d\n"
			"Demons bowled: %d    Suffocated: %d    Melted: %d\n"
			"Eyeballs squished: %d    Eyeballs punted: %d",
			kickGibs, tidied, farts, doors, bowled, gasKills, melts,
			eyes, eyepunts);
	}

	override void WorldLoaded(WorldEvent e)
	{
		if (e.IsSaveGame) return;
		Console.Printf("\c[Gold]TIP:\c- %s",
			kTips[random[FPBTip](0, kTips.Size() - 1)]);
	}

	override void WorldUnloaded(WorldEvent e)
	{
		if (kickGibs + gasKills + melts + doors + farts + eyes + bowled
			+ eyepunts + tidied == 0)
			return;
		let h = FPB_Herald(EventHandler.Find("FPB_Herald"));
		if (h) h.card = BuildCard();
	}

	override void NetworkProcess(ConsoleEvent e)
	{
		if (e.Name == "fpb_stats")
			Console.Printf("%s", BuildCard());
	}

	override void WorldThingDied(WorldEvent e)
	{
		let mo = e.Thing;
		if (mo == null || mo.player != null) return;

		// Barrels are pressurized with industrial effluent. Now you know.
		if (mo is "ExplosiveBarrel")
		{
			let pc = Actor.Spawn("StinkCloud", mo.pos + (0, 0, 16));
			if (pc)
			{
				pc.target = mo.target;
				pc.scale = (0.5, 0.5);
			}
			return;
		}
		if (!mo.bIsMonster) return;

		Name dt = mo.DamageTypeReceived;
		if (dt == 'Kick')
		{
			BurstIntoGiblets(mo);
			AddGunk(mo);
			kickGibs++;
			for (int i = 0; i < kMilestones.Size(); i++)
			{
				if (kickGibs == kMilestones[i])
				{
					Console.Printf("\c[Red]%s\c-", kTitles[i]);
					break;
				}
			}
			// streak accounting: three in four seconds earns a title
			kickTics.Push(level.maptime);
			while (kickTics.Size() > 0
				&& level.maptime - kickTics[0] > 140)
			{
				kickTics.Delete(0);
			}
			if (kickTics.Size() >= 5)
			{
				Console.Printf(
					"\c[Gold]FULL COMPOST. SOMEBODY OPEN A WINDOW.\c-");
				kickTics.Clear();
			}
			else if (kickTics.Size() == 3)
			{
				Console.Printf("\c[Gold]HAT TRICK.\c-");
			}
			// the occasional editorial remark, strictly rationed
			if (random[FPBQuip](0, 99) < 8
				&& level.maptime - lastQuipTic > 350)
			{
				lastQuipTic = level.maptime;
				Console.Printf("\c[DarkGray]%s\c-",
					kQuips[random[FPBQuip](0, kQuips.Size() - 1)]);
			}
		}
		else if (dt == 'FartGas')
		{
			gasKills++;
			mo.A_SetTranslation('PoisonSkin');
			mo.A_StartSound("butt/choke", CHAN_VOICE);
		}
		else if (dt == 'FartAcid')
		{
			melts++;
			let m = AcidMelter(Actor.Spawn("AcidMelter", mo.pos));
			if (m) m.tracer = mo;
		}

		// Posthumous punctuation: most demons have one last thing to say.
		// Pitch scales with body mass. Physics.
		let cvt = CVar.FindCVar('fpb_deathtoots');
		if ((cvt == null || cvt.GetInt() != 0)
			&& random[FPBToot](0, 99) < 70)
		{
			let mt = FPB_MiniToot(Actor.Spawn("FPB_MiniToot",
				mo.pos + (0, 0, max(6, mo.height * 0.25))));
			if (mt)
			{
				if (mo.mass >= 600) mt.tootPitch = 0.55;
				else if (mo.mass >= 200) mt.tootPitch = 0.8;
				else mt.tootPitch = 1.25 + random[FPBToot](0, 30) / 100.0;
			}
		}
	}

	// A gib right in your face leaves evidence on the lens for a few seconds.
	void AddGunk(Actor mo)
	{
		let cv = CVar.FindCVar('fpb_screengunk');
		if (cv && cv.GetInt() == 0) return;
		if (!playeringame[consoleplayer]) return;
		let pmo = players[consoleplayer].mo;
		if (pmo == null || mo.Distance3D(pmo) > 170) return;

		int n = 2 + random[FPBGunk](0, 2);
		for (int i = 0; i < n; i++)
		{
			int slot = random[FPBGunk](0, 7);
			gunkBorn[slot] = max(1, level.maptime);
			gunkX[slot] = 0.15 + random[FPBGunk](0, 100) / 142.0;
			gunkY[slot] = 0.15 + random[FPBGunk](0, 100) / 142.0;
			gunkS[slot] = 0.5 + random[FPBGunk](0, 100) / 100.0;
			gunkT[slot] = random[FPBGunk](0, 1);
		}
	}

	override void RenderOverlay(RenderEvent e)
	{
		for (int i = 0; i < 8; i++)
		{
			if (gunkBorn[i] <= 0) continue;
			int age = level.maptime - gunkBorn[i];
			if (age < 0 || age > 100) continue;
			double a = 0.85 * (1.0 - age / 100.0);
			TextureID t = TexMan.CheckForTexture(
				gunkT[i] == 0 ? "GUNK1" : "GUNK2", TexMan.Type_Any);
			if (!t.IsValid()) continue;
			int size = int(Screen.GetHeight() * 0.35 * gunkS[i]);
			Screen.DrawTexture(t, false,
				gunkX[i] * Screen.GetWidth(), gunkY[i] * Screen.GetHeight(),
				DTA_CenterOffset, true, DTA_Alpha, a,
				DTA_DestWidth, size, DTA_DestHeight, size);
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

		// and once in a great while, the universe tips its hat
		if (random[FPBGore](0, 39) == 0)
		{
			Actor.Spawn("FPB_GoldenKernel", mo.pos + (0, 0, 28));
		}
	}
}

// The last word, delivered a comedic beat after death.
class FPB_MiniToot : Actor
{
	double tootPitch;

	Default
	{
		+NOBLOCKMAP
		+NOGRAVITY
		+NOINTERACTION
		+FORCEXYBILLBOARD
		RenderStyle "Translucent";
		Alpha 0.75;
		Scale 0.45;
	}
	States
	{
	Spawn:
		TNT1 A 12 NoDelay;
		TNT1 A 0 A_Jump(128, 2);
		TNT1 A 8;
		TNT1 A 0
		{
			A_StartSound("butt/fart", CHAN_BODY, 0,
				tootPitch < 0.8 ? 0.85 : 0.55, ATTN_NORM, tootPitch);
		}
		FART A 3 Bright;
		FART B 3 Bright;
		FART C 3 Bright A_FadeOut(0.2);
		Wait;
	}
}

// One gibbing in forty produces this. Nobody knows why. Eat it anyway.
class FPB_GoldenKernel : CustomInventory
{
	Default
	{
		Radius 10;
		Height 16;
		+COUNTITEM
		+NOGRAVITY
		+FLOATBOB
		Scale 1.1;
	}

	override String PickupMessage()
	{
		return "THE GOLDEN KERNEL. YOU FEEL... CHOSEN.";
	}

	States
	{
	Spawn:
		KERN A 6 Bright;
		KERN B 6 Bright;
		Loop;
	Pickup:
		TNT1 A 0
		{
			A_StartSound("butt/pickup", CHAN_AUTO);
			A_GiveInventory("Gas", 40);
			HealThing(40, 0);
		}
		Stop;
	}
}

// Carries the stat card across the level change and reads it out on arrival.
class FPB_Herald : EventHandler
{
	String card;

	override void WorldLoaded(WorldEvent e)
	{
		if (e.IsSaveGame || card.Length() == 0) return;
		Console.Printf("%s", card);
		card = "";
	}
}

// Rides along with a punted demon and knocks down whatever it plows into.
// Two victims is a DOUBLE, three or more is a STRIKE.
class FPB_BowlingWatcher : Actor
{
	Array<Actor> struck;
	int life;

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
		let v = tracer;
		life++;
		if (v == null || life > 105)
		{
			Finish();
			return;
		}
		double spd = v.vel.xy.Length();
		if (spd < 6)
		{
			Finish();
			return;
		}
		SetOrigin(v.pos, true);

		BlockThingsIterator it = BlockThingsIterator.Create(v, v.radius + 24);
		while (it.Next())
		{
			let mo = it.thing;
			if (mo == null || mo == v || mo == target) continue;
			if (!mo.bIsMonster || !mo.bShootable || mo.health <= 0) continue;
			if (struck.Find(mo) != struck.Size()) continue;
			if (v.Distance2D(mo) > v.radius + mo.radius + 24) continue;

			struck.Push(mo);
			double ang = v.AngleTo(mo);
			mo.vel = (
				mo.vel.x + cos(ang) * spd * 0.7,
				mo.vel.y + sin(ang) * spd * 0.7,
				mo.vel.z + 4
			);
			mo.DamageMobj(v, target, 45, 'Kick', DMG_THRUSTLESS);
			mo.A_StartSound("boot/splat", CHAN_AUTO, 0, 0.8);
		}
	}

	void Finish()
	{
		if (struck.Size() >= 2)
		{
			FPB_GoreHandler.Bump('bowled', struck.Size());
			Console.Printf("\c[Gold]%s\c-", struck.Size() >= 3
				? "STRIKE. THEY FELT THAT ONE IN HELL."
				: "DOUBLE! DEMON BOWLING.");
		}
		else if (struck.Size() == 1)
		{
			FPB_GoreHandler.Bump('bowled', 1);
		}
		Destroy();
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

// It rolls free, it comes to rest, it stares. Walk over it to squish it —
// or kick it (with nothing else in range) to send it downfield, squeaking.
class FPB_Eyeball : CustomInventory
{
	Default
	{
		Radius 6;
		Height 8;
		+DROPOFF
		Scale 0.9;
		BounceType "Doom";
		BounceFactor 0.65;
		BounceSound "gore/bounce";
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
		TNT1 A 0
		{
			A_StartSound("gore/bounce", CHAN_AUTO, 0, 0.9);
			FPB_GoreHandler.Bump('eyes');
		}
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
