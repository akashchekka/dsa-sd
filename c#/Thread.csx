using System;
using System.Threading;

public class Program {
    static int Counter = 0;
    static readonly object _lock = new object();

    static void Increment() {
        for (int i = 0; i < 1_000_000; i++) {
            Counter++;
        }
    }

    static void SafeIncrement() {
        for (int i = 0; i < 1_000_000; i++) {
            lock (_lock) {
                Counter++;
            }
        }
    }

    public static void Main() {
        var t1 = new Thread(SafeIncrement);
        var t2 = new Thread(SafeIncrement);

        t1.Start();
        t2.Start();

        t1.Join();
        t2.Join();

        Console.WriteLine(Counter);
    }
}

Program.Main()