// Death flavor, applied from the outside so it works on ANY monster set
// (Freedoom, Doom, other mods) without touching their classes:
//   Kick     -> extra giblet shower on top of the engine's extreme death
//   FartGas  -> victim keels over green (suffocated)
//   FartAcid -> corpse squashes into a bubbling goo pile (melted)
class FPB_GoreHandler : EventHandler
{
	override void WorldThingDied(WorldEvent e)
	{
		let mo = e.Thing;
		if (mo == null || mo.player != null || !mo.bIsMonster) return;

		Name dt = mo.DamageTypeReceived;
		if (dt == 'Kick')
		{
			BurstIntoGiblets(mo);
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
		int mult = 2;
		let cv = CVar.FindCVar('fpb_gore');
		if (cv) mult = clamp(cv.GetInt(), 0, 4);
		if (mult <= 0) return;

		mo.A_StartSound("boot/gib", CHAN_AUTO);
		int n = (4 + random[FPBGore](0, 4)) * mult;
		for (int i = 0; i < n; i++)
		{
			let chunk = Actor.Spawn("MeatChunk", mo.pos + (0, 0, max(8, mo.height * 0.5)));
			if (chunk == null) continue;
			chunk.vel = (
				random[FPBGore](-100, 100) / 16.0,
				random[FPBGore](-100, 100) / 16.0,
				random[FPBGore](30, 110) / 14.0
			);
			double s = 0.6 + random[FPBGore](0, 70) / 100.0;
			chunk.scale = (s, s);
		}
	}
}

// A flying piece of former demon. Tumbles, bounces wetly, settles as a splat.
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
