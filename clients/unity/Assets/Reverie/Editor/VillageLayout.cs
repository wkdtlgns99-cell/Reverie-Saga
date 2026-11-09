using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;

namespace ReverieSaga
{
    [Serializable]
    internal sealed class VillageLayout
    {
        [Serializable]
        internal sealed class Placement
        {
            public string kind;
            public int x, y, variant, facing;
        }

        internal const int RoomSize = 5;
        internal const string SeedPattern = @"\A[0-9a-f]{64}\z";
        public int version, gate_x, gate_y;
        public string seed, terrain;
        public Placement[] village, dungeon;

        internal void Validate(string[] rows)
        {
            if (version != 1 || !Regex.IsMatch(seed ?? "", SeedPattern) || String.IsNullOrEmpty(terrain) ||
                gate_y < 1 || gate_y != rows.Length - 1 || gate_x <= 0 || gate_x >= rows[0].Length - 1 ||
                rows[gate_y][gate_x] != '#' || rows[gate_y - 1][gate_x] != '.')
                throw new IOException("VILLAGE_LAYOUT");
            ValidateArea(village, rows[0].Length, rows.Length, false);
            ValidateArea(dungeon, RoomSize, RoomSize, true);
        }

        static void ValidateArea(Placement[] items, int width, int height, bool room)
        {
            if (items == null || items.Length > width * height + (room ? 1 : 0))
                throw new IOException("VILLAGE_LAYOUT_COUNT");
            var occupied = new HashSet<int>();
            int special = 0;
            foreach (var item in items)
            {
                if (item == null || item.x < 0 || item.x >= width || item.y < 0 || item.y >= height ||
                    item.variant < 0 || item.variant > (room ? 1 : 2) || item.facing < 0 || item.facing > 3)
                    throw new IOException("VILLAGE_LAYOUT_POSITION");
                switch (item.kind)
                {
                    case "gate" when !room:
                        special++;
                        break;
                    case "orc" when room:
                        special++;
                        continue;
                    case "road" when !room: case "house" when !room: case "wall" when !room:
                    case "tree" when !room: case "rock" when !room:
                    case "dungeon-wall" when room: case "dungeon-floor" when room:
                        break;
                    default:
                        throw new IOException("VILLAGE_LAYOUT_KIND");
                }
                if (!occupied.Add(item.y * width + item.x))
                    throw new IOException("VILLAGE_LAYOUT_OVERLAP");
            }
            if (special != 1)
                throw new IOException("VILLAGE_LAYOUT_SPECIAL");
        }
    }

}
