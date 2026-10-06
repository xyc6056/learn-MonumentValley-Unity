using System.Collections.Generic;

public static class WalkGraph
{
    public static List<Walkable> FindPath(Walkable start, Walkable goal)
    {
        if (start == null || goal == null)
            return null;

        if (start == goal)
            return new List<Walkable> { start };

        Queue<Walkable> frontier = new Queue<Walkable>();
        HashSet<Walkable> visited = new HashSet<Walkable>();
        Dictionary<Walkable, Walkable> cameFrom = new Dictionary<Walkable, Walkable>();

        frontier.Enqueue(start);
        visited.Add(start);

        while (frontier.Count > 0)
        {
            Walkable current = frontier.Dequeue();
            if (current == null || current.possiblePaths == null)
                continue;

            foreach (WalkPath path in current.possiblePaths)
            {
                if (path == null || !path.active)
                    continue;

                Walkable next = current.GetPathTarget(path);
                if (next == null || visited.Contains(next))
                    continue;

                visited.Add(next);
                cameFrom[next] = current;

                if (next == goal)
                    return BuildPath(start, goal, cameFrom);

                frontier.Enqueue(next);
            }
        }

        return null;
    }

    private static List<Walkable> BuildPath(Walkable start, Walkable goal, Dictionary<Walkable, Walkable> cameFrom)
    {
        List<Walkable> path = new List<Walkable>();
        Walkable current = goal;

        while (current != null)
        {
            path.Add(current);
            if (current == start)
                break;

            Walkable previous;
            if (!cameFrom.TryGetValue(current, out previous))
                return null;

            current = previous;
        }

        path.Reverse();
        return path;
    }
}
