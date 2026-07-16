// The Booter: like a space marine, but the business end points down (and, later, backwards).
class BooterPlayer : DoomPlayer
{
	Default
	{
		Player.DisplayName "Booter";
		Player.StartItem "Boot";
		Player.StartItem "Gas", 40;      // pre-gassed, so finding the Cheeks is instantly fun
		Player.WeaponSlot 1, "Boot";
		Player.WeaponSlot 2, "CheeksOfDoom";
	}
}
