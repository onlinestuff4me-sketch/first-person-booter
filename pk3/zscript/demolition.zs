// The demolition layer. Watches every destructible wall in the level and
// dresses its damage in physics: dust and chips per hit, a STRUCTURAL
// DAMAGE warning below half health, and a full rubble blowout at zero —
// timed to cover the geometry snapping open underneath it.
class FPB_Demolition : EventHandler
{
	override void WorldLineDamaged(WorldEvent e)
	{
		let l = e.DamageLine;
		if (l == null) return;

		// per-hit feedback at the point of impact
		DustAt(e.DamagePosition, 0.6);
		if (random[FPBDemo](0, 99) < 65)
			SplinterBurst(e.DamagePosition, 0, 2, "FPB_Rubble");

		if (l.health > 0)
		{
			int orig = level.GetUDMFInt(UDMF_Line, l.Index(), 'health');
			if (orig > 0)
			{
				int half = orig / 2;
				if (l.health <= half && l.health + e.Damage > half)
					Console.Printf("\c[DarkGray]STRUCTURAL DAMAGE.\c-");
			}
			return;
		}

		Blowout(l);
	}

	void Blowout(Line l)
	{
		vector2 a = l.v1.p;
		vector2 b = l.v2.p;
		vector2 mid = (a + b) / 2;
		double fz = 0;
		if (l.frontsector) fz = l.frontsector.floorplane.ZatPoint(mid);

		vector2 delta = b - a;
		double len = delta.Length();
		if (len <= 1) return;
		vector2 dir = delta / len;
		vector2 nrm = (dir.y, -dir.x);

		int chunks = clamp(int(len / 12), 8, 40);
		for (int i = 0; i < chunks; i++)
		{
			double t = frandom[FPBDemo](0.05, 0.95);
			vector2 sp = a + dir * (len * t);
			double side = (random[FPBDemo](0, 1) == 0) ? 1 : -1;
			let r = Actor.Spawn("FPB_Rubble",
				(sp.x, sp.y, fz + frandom[FPBDemo](8, 88)));
			if (r == null) continue;
			r.vel = (
				nrm.x * side * frandom[FPBDemo](3, 9),
				nrm.y * side * frandom[FPBDemo](3, 9),
				frandom[FPBDemo](2, 7)
			);
			double s = frandom[FPBDemo](0.5, 1.3);
			r.scale = (s, s);
		}
		for (int i = 0; i < 5; i++)
		{
			vector2 sp = a + dir * (len * (0.1 + 0.2 * i));
			DustAt((sp.x, sp.y, fz + 36), 1.1);
		}

		let boomer = Actor.Spawn("FPB_DustPuff", (mid.x, mid.y, fz + 40));
		if (boomer)
		{
			boomer.A_StartSound("wall/collapse", CHAN_AUTO);
			boomer.A_Quake(5, 24, 0, 640);
		}
		FPB_GoreHandler.Bump('walls');
		Console.Printf("\c[Gold]BREACH! THE WALL HAD ENOUGH.\c-");
	}

	static void SplinterBurst(vector3 p, double ang, int n,
		String cls = "FPB_DoorSplinter")
	{
		for (int i = 0; i < n; i++)
		{
			let s = Actor.Spawn(cls, p + (0, 0, frandom[FPBDemo](-20, 20)));
			if (s == null) continue;
			double a2 = ang + frandom[FPBDemo](-70, 70);
			double spd = frandom[FPBDemo](3, 10);
			s.vel = (cos(a2) * spd, sin(a2) * spd, frandom[FPBDemo](2, 8));
			double sc = frandom[FPBDemo](0.5, 1.1);
			s.scale = (sc, sc);
		}
	}

	static void DustAt(vector3 p, double size)
	{
		let d = Actor.Spawn("FPB_DustPuff", p);
		if (d) d.scale = (0.3 + 0.4 * size, 0.3 + 0.4 * size);
	}
}

// A shard of former door. Clatters woodenly.
class FPB_DoorSplinter : Actor
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
		Radius 4;
		Height 4;
		Gravity 0.8;
		Damage 0;
		BounceType "Doom";
		BounceFactor 0.4;
		WallBounceFactor 0.5;
		BounceCount 3;
		BounceSound "wood/snap";
	}
	States
	{
	Spawn:
		SPLN A 3;
		SPLN B 3;
		SPLN C 3;
		SPLN D 3;
		Loop;
	Death:
		SPLN E 240;
		SPLN E 2 A_FadeOut(0.05);
		Wait;
	}
}

// A chunk of former wall. Knocks stonily.
class FPB_Rubble : FPB_DoorSplinter
{
	Default
	{
		Radius 5;
		Height 5;
		BounceSound "rock/tap";
	}
	States
	{
	Spawn:
		RUBL A 3;
		RUBL B 3;
		RUBL C 3;
		RUBL D 3;
		Loop;
	Death:
		RUBL E 350;
		RUBL E 2 A_FadeOut(0.04);
		Wait;
	}
}

// Construction-grade dust. Rises, spreads, settles on everything.
class FPB_DustPuff : Actor
{
	Default
	{
		+NOBLOCKMAP
		+NOGRAVITY
		+NOCLIP
		+NOTELEPORT
		+FORCEXYBILLBOARD
		RenderStyle "Translucent";
		Alpha 0.55;
		Scale 0.7;
	}
	States
	{
	Spawn:
		DUST A 4 A_DustDrift;
		DUST B 4 A_DustDrift;
		DUST C 4 A_DustDrift;
		DUST C 3 A_FadeOut(0.07);
		Wait;
	}

	void A_DustDrift()
	{
		vel = (vel.x, vel.y, 0.5);
		A_SetScale(scale.x + 0.06);
	}
}
