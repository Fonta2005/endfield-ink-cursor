using System;
using System.Collections.Concurrent;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using Microsoft.Win32;

namespace SiInkClick
{
    static class Native
    {
        [DllImport("user32.dll", SetLastError = true)]
        public static extern IntPtr SetWindowsHookEx(int idHook, HookProc lpfn, IntPtr hMod, uint dwThreadId);
        [DllImport("user32.dll")]
        public static extern bool UnhookWindowsHookEx(IntPtr hhk);
        [DllImport("user32.dll")]
        public static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);
        [DllImport("kernel32.dll", CharSet = CharSet.Auto)]
        public static extern IntPtr GetModuleHandle(string lpModuleName);
        [DllImport("user32.dll")]
        public static extern IntPtr GetDC(IntPtr hWnd);
        [DllImport("user32.dll")]
        public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);
        [DllImport("gdi32.dll")]
        public static extern IntPtr CreateCompatibleDC(IntPtr hdc);
        [DllImport("gdi32.dll")]
        public static extern bool DeleteDC(IntPtr hdc);
        [DllImport("gdi32.dll")]
        public static extern IntPtr SelectObject(IntPtr hdc, IntPtr hgdiobj);
        [DllImport("gdi32.dll")]
        public static extern bool DeleteObject(IntPtr hObject);
        [DllImport("user32.dll", SetLastError = true)]
        public static extern bool UpdateLayeredWindow(IntPtr hwnd, IntPtr hdcDst, ref POINT pptDst, ref SIZE psize, IntPtr hdcSrc, ref POINT pptSrc, int crKey, ref BLENDFUNCTION pblend, int dwFlags);
        [DllImport("user32.dll")]
        public static extern bool SetProcessDPIAware();

        [StructLayout(LayoutKind.Sequential)]
        public struct POINT { public int X; public int Y; }
        [StructLayout(LayoutKind.Sequential)]
        public struct SIZE { public int cx; public int cy; }
        [StructLayout(LayoutKind.Sequential, Pack = 1)]
        public struct BLENDFUNCTION { public byte BlendOp; public byte BlendFlags; public byte SourceConstantAlpha; public byte AlphaFormat; }
        [StructLayout(LayoutKind.Sequential)]
        public struct MSLLHOOKSTRUCT { public POINT pt; public uint mouseData; public uint flags; public uint time; public IntPtr dwExtraInfo; }

        public delegate IntPtr HookProc(int nCode, IntPtr wParam, IntPtr lParam);

        public const int WH_MOUSE_LL = 14;
        public const int WM_LBUTTONDOWN = 0x0201;
        public const int WM_RBUTTONDOWN = 0x0204;
        public const int WM_MBUTTONDOWN = 0x0207;
        public const int WM_XBUTTONDOWN = 0x020B;
        public const int WS_EX_LAYERED = 0x00080000;
        public const int WS_EX_TRANSPARENT = 0x00000020;
        public const int WS_EX_TOOLWINDOW = 0x00000080;
        public const int WS_EX_TOPMOST = 0x00000008;
        public const int WS_EX_NOACTIVATE = 0x08000000;
        public const int ULW_ALPHA = 0x00000002;
        public const byte AC_SRC_ALPHA = 1;
    }

    // Water ripple: refraction of the captured backdrop + crest shading (works on white and dark)
    class DropForm : Form
    {
        const double TOTAL_MS = 720;   // whole animation length

        readonly int side;
        readonly Bitmap src;
        readonly byte[] srcBytes;
        double hiK = 18.0, loK = 18.0;
        Timer timer;
        double phase0;
        System.Diagnostics.Stopwatch clock;

        public DropForm(Point center, int sidePx, string bgMode)
        {
            side = sidePx;
            FormBorderStyle = FormBorderStyle.None;
            ShowInTaskbar = false;
            TopMost = true;
            StartPosition = FormStartPosition.Manual;
            Bounds = new Rectangle(center.X - side / 2, center.Y - side / 2, side, side);
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.UserPaint, true);

            src = new Bitmap(side, side, PixelFormat.Format32bppArgb);
            if (bgMode == "screen")
            {
                using (Graphics g = Graphics.FromImage(src))
                    g.CopyFromScreen(center.X - side / 2, center.Y - side / 2, 0, 0, new Size(side, side), CopyPixelOperation.SourceCopy);
            }
            else
            {
                using (Graphics g = Graphics.FromImage(src))
                using (SolidBrush b1 = new SolidBrush(Color.White))
                using (SolidBrush b2 = new SolidBrush(Color.FromArgb(255, 18, 24, 30)))
                {
                    g.FillRectangle(b1, 0, 0, side, side);
                    if (bgMode == "dark") g.FillRectangle(b2, 0, 0, side, side);
                    if (bgMode == "split")
                    {
                        g.FillRectangle(b2, 0, side / 2, side, side / 2);
                        using (Font f = new Font("Consolas", 10f))
                        using (SolidBrush tb = new SolidBrush(Color.FromArgb(90, 0, 0, 0)))
                            for (int yy = 8; yy < side; yy += 14) g.DrawString("The quick brown fox 0123456789", f, tb, 4, yy);
                    }
                }
            }
            BitmapData bd = src.LockBits(new Rectangle(0, 0, side, side), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
            srcBytes = new byte[Math.Abs(bd.Stride) * side];
            Marshal.Copy(bd.Scan0, srcBytes, 0, srcBytes.Length);
            src.UnlockBits(bd);

            // measure how bright the backdrop is, so the ring can pick the side of
            // the contrast that is actually visible (dark ring on white, glow on black)
            long sum = 0; int cnt = 0;
            for (int i = 0; i + 3 < srcBytes.Length; i += 4 * 7)
            {
                sum += (long)(srcBytes[i] * 0.114 + srcBytes[i + 1] * 0.587 + srcBytes[i + 2] * 0.299);
                cnt++;
            }
            double lum = cnt > 0 ? (sum / (double)cnt) / 255.0 : 0.5;

            if (lum > 0.55) { hiK = 5.0; loK = 34.0; }          // light backdrop: shadow ring
            else if (lum < 0.33) { hiK = 30.0; loK = 6.0; }      // dark backdrop: light ring
            else { double u = (lum - 0.33) / (0.22); hiK = 30.0 - 25.0 * u; loK = 6.0 + 28.0 * u; }

            phase0 = ((center.X * 7 + center.Y * 13) % 100) / 100.0;
            clock = new System.Diagnostics.Stopwatch();
            timer = new Timer();
            timer.Interval = 8;
            timer.Tick += new EventHandler(OnTick);
        }

        protected override CreateParams CreateParams
        {
            get
            {
                CreateParams cp = base.CreateParams;
                cp.ExStyle |= Native.WS_EX_LAYERED | Native.WS_EX_TRANSPARENT | Native.WS_EX_TOOLWINDOW |
                              Native.WS_EX_TOPMOST | Native.WS_EX_NOACTIVATE;
                return cp;
            }
        }

        protected override bool ShowWithoutActivation { get { return true; } }

        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            Draw(0.0);
            clock.Start();
            timer.Start();
        }

        double lastMs;

        void OnTick(object sender, EventArgs e)
        {
            double ms = clock.Elapsed.TotalMilliseconds;
            double t = ms / TOTAL_MS;
            if (t >= 1.0) { timer.Stop(); Close(); return; }
            if (ms - lastMs < 11.0) return;   // cap at ~90 fps so we do not overdraw
            lastMs = ms;
            Draw(t);
        }

        unsafe void Draw(double t)
        {
            if (t < 0) t = 0; if (t > 1) t = 1;
            // the ring keeps travelling outward at a constant rate and only loses
            // contrast: it dissolves where it is, it never shrinks or snaps out.
            double Rf = 9 + 13 * t;
            double vis = (t - 0.40) / 0.60;            // 1 -> 0 over the last 60%
            if (vis < 0) vis = 0; if (vis > 1) vis = 1;
            double V = 1.0 - vis * vis * (3.0 - 2.0 * vis);   // smooth dissolve, V(1)=0
            double attack = t / 0.05;
            if (attack > 1) attack = 1;
            attack = attack * attack * (3.0 - 2.0 * attack);
            V *= attack;

            double amp = 7.4 * (1.0 - 0.30 * t) * (1 - Math.Exp(-14 * t)) * (0.30 + 0.70 * V);
            double lambda = 9.5;
            double k = 6.2831853 / lambda;
            double gain = 1.8 * (0.35 + 0.65 * V);
            double fade = V;
            double c = side / 2.0;

            Bitmap dst = new Bitmap(side, side, PixelFormat.Format32bppPArgb);
            BitmapData bd = dst.LockBits(new Rectangle(0, 0, side, side), ImageLockMode.WriteOnly, PixelFormat.Format32bppPArgb);
            int stride = Math.Abs(bd.Stride);
            byte[] outB = new byte[stride * side];

            // light direction (from upper-left, above the surface)
            double Lx = -0.50, Ly = -0.66, Lz = 0.56;
            double ln = Math.Sqrt(Lx * Lx + Ly * Ly + Lz * Lz);
            Lx /= ln; Ly /= ln; Lz /= ln;

            for (int y = 0; y < side; y++)
            {
                int rowoff = y * stride;
                for (int x = 0; x < side; x++)
                {
                    double dx = x - c, dy = y - c;
                    double r = Math.Sqrt(dx * dx + dy * dy) + 1e-6;
                    double ux = dx / r, uy = dy / r;

                    // single travelling crest (one bump) -> one ring, not a dense set of rings
                    double h = 0, dh = 0;
                    double dr = r - Rf;
                    double sig = lambda * 0.34;
                    double env = Math.Exp(-(dr * dr) / (2.0 * sig * sig));
                    double ramp = (r - Rf * 0.35) / Math.Max(3.0, Rf * 0.30);
                    if (ramp < 0) ramp = 0; if (ramp > 1) ramp = 1;
                    h = amp * env * ramp;
                    dh = amp * env * (-dr / (sig * sig)) * ramp;

                    double sx = x + ux * dh * gain;
                    double sy = y + uy * dh * gain;
                    if (sx < 0) sx = 0; if (sx > side - 1.001) sx = side - 1.001;
                    if (sy < 0) sy = 0; if (sy > side - 1.001) sy = side - 1.001;
                    int ix = (int)sx, iy = (int)sy;
                    double fx = sx - ix, fy = sy - iy;

                    int i00 = iy * stride + ix * 4, i10 = i00 + 4, i01 = i00 + stride, i11 = i01 + 4;
                    double b = srcBytes[i00] * (1 - fx) * (1 - fy) + srcBytes[i10] * fx * (1 - fy) + srcBytes[i01] * (1 - fx) * fy + srcBytes[i11] * fx * fy;
                    double g = srcBytes[i00 + 1] * (1 - fx) * (1 - fy) + srcBytes[i10 + 1] * fx * (1 - fy) + srcBytes[i01 + 1] * (1 - fx) * fy + srcBytes[i11 + 1] * fx * fy;
                    double rr = srcBytes[i00 + 2] * (1 - fx) * (1 - fy) + srcBytes[i10 + 2] * fx * (1 - fy) + srcBytes[i01 + 2] * (1 - fx) * fy + srcBytes[i11 + 2] * fx * fy;

                    // additive +/- offset instead of multiplying the backdrop:
                    // a bright edge and a dark edge sit next to each other, so the ring
                    // stays visible on white, on black and on any colour in between.
                    double s = dh * 2.0;
                    if (s > 1.0) s = 1.0; if (s < -1.0) s = -1.0;
                    double add = s > 0 ? s * hiK : s * loK;   // asymmetric: shadow side on light bg

                    double wr = rr + add * 0.96;
                    double wg = g + add * 1.00;
                    double wb = b + add * 1.03;

                    // Only the distorted band is drawn (alpha follows local wave strength),
                    // so there is no square patch and no bright rim at the border.
                    // fixed-width ring (independent of radius) -> thin ring at any size
                    double ringW = 2.0;
                    double edge = Math.Exp(-(dr * dr) / (2.0 * ringW * ringW));
                    if (r > Rf + lambda * 2.2) edge = 0;

                    int o = rowoff + x * 4;
                    if (wr < 0) wr = 0; if (wr > 255) wr = 255;
                    if (wg < 0) wg = 0; if (wg > 255) wg = 255;
                    if (wb < 0) wb = 0; if (wb > 255) wb = 255;
                    outB[o] = (byte)wb; outB[o + 1] = (byte)wg; outB[o + 2] = (byte)wr;
                    outB[o + 3] = (byte)(255 * fade * edge);
                }
            }
            Marshal.Copy(outB, 0, bd.Scan0, outB.Length);
            dst.UnlockBits(bd);
            ApplyLayered(dst);
            dst.Dispose();
        }

        void ApplyLayered(Bitmap bmp)
        {
            IntPtr screenDc = Native.GetDC(IntPtr.Zero);
            IntPtr memDc = Native.CreateCompatibleDC(screenDc);
            IntPtr hBitmap = IntPtr.Zero;
            IntPtr oldBitmap = IntPtr.Zero;
            try
            {
                hBitmap = bmp.GetHbitmap(Color.FromArgb(0));
                oldBitmap = Native.SelectObject(memDc, hBitmap);
                Native.SIZE size = new Native.SIZE();
                size.cx = bmp.Width; size.cy = bmp.Height;
                Native.POINT srcPt = new Native.POINT();
                Native.POINT dstPt = new Native.POINT();
                dstPt.X = Left; dstPt.Y = Top;
                Native.BLENDFUNCTION blend = new Native.BLENDFUNCTION();
                blend.BlendOp = 0; blend.BlendFlags = 0;
                blend.SourceConstantAlpha = 255;
                blend.AlphaFormat = Native.AC_SRC_ALPHA;
                Native.UpdateLayeredWindow(Handle, screenDc, ref dstPt, ref size, memDc, ref srcPt, 0, ref blend, Native.ULW_ALPHA);
            }
            finally
            {
                if (hBitmap != IntPtr.Zero)
                {
                    Native.SelectObject(memDc, oldBitmap);
                    Native.DeleteObject(hBitmap);
                }
                Native.DeleteDC(memDc);
                Native.ReleaseDC(IntPtr.Zero, screenDc);
            }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing && src != null) src.Dispose();
            base.Dispose(disposing);
        }
    }

    class TrayContext : ApplicationContext
    {
        NotifyIcon icon;
        Timer drain;
        ConcurrentQueue<Point> pts = new ConcurrentQueue<Point>();
        static IntPtr hook = IntPtr.Zero;
        static Native.HookProc proc;
        bool enabled = true;
        int side;

        const string RunKey = @"Software\Microsoft\Windows\CurrentVersion\Run";
        const string AppName = "SiInkClick";

        public TrayContext()
        {
            float dpi;
            using (Graphics g = Graphics.FromHwnd(IntPtr.Zero)) dpi = g.DpiX / 96f;
            side = (int)(76 * dpi);

            icon = new NotifyIcon();
            icon.Icon = LoadAppIcon();
            icon.Text = "\u7940 \u00b7 \u6c34\u6ce2\u70b9\u51fb\u7279\u6548";
            ContextMenuStrip menu = new ContextMenuStrip();
            ToolStripMenuItem miToggle = new ToolStripMenuItem("\u5f00\u542f\u70b9\u51fb\u7279\u6548");
            miToggle.Checked = true;
            miToggle.Click += delegate { enabled = !enabled; miToggle.Checked = enabled; };
            ToolStripMenuItem miAuto = new ToolStripMenuItem("\u5f00\u673a\u81ea\u542f");
            miAuto.Checked = IsAutoStart();
            miAuto.Click += delegate { SetAutoStart(!IsAutoStart()); miAuto.Checked = IsAutoStart(); };
            ToolStripMenuItem miTest = new ToolStripMenuItem("\u8bd5\u4e00\u4e0b");
            miTest.Click += delegate { Spawn(Cursor.Position); };
            ToolStripMenuItem miExit = new ToolStripMenuItem("\u9000\u51fa");
            miExit.Click += delegate { ExitThread(); };
            menu.Items.Add(miToggle);
            menu.Items.Add(miAuto);
            menu.Items.Add(miTest);
            menu.Items.Add(new ToolStripSeparator());
            menu.Items.Add(miExit);
            icon.ContextMenuStrip = menu;
            icon.Visible = true;

            proc = new Native.HookProc(HookCallback);
            hook = Native.SetWindowsHookEx(Native.WH_MOUSE_LL, proc, Native.GetModuleHandle(null), 0);

            drain = new Timer();
            drain.Interval = 15;
            drain.Tick += delegate { Drain(); };
            drain.Start();
        }

        static Icon LoadAppIcon()
        {
            Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream("AppIcon");
            if (s != null) return new Icon(s);
            return SystemIcons.Application;
        }

        static IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0)
            {
                int msg = wParam.ToInt32();
                if (msg == Native.WM_LBUTTONDOWN || msg == Native.WM_RBUTTONDOWN || msg == Native.WM_MBUTTONDOWN || msg == Native.WM_XBUTTONDOWN)
                {
                    Native.MSLLHOOKSTRUCT info = (Native.MSLLHOOKSTRUCT)Marshal.PtrToStructure(lParam, typeof(Native.MSLLHOOKSTRUCT));
                    TrayContext ctx = TrayContext.Current;
                    if (ctx != null && ctx.enabled) ctx.pts.Enqueue(new Point(info.pt.X, info.pt.Y));
                }
            }
            return Native.CallNextHookEx(hook, nCode, wParam, lParam);
        }

        public static TrayContext Current;

        void Drain()
        {
            Point p;
            while (pts.TryDequeue(out p)) Spawn(p);
        }

        void Spawn(Point p)
        {
            DropForm f = new DropForm(p, side, "screen");
            f.Show();
        }

        static bool IsAutoStart()
        {
            using (RegistryKey k = Registry.CurrentUser.OpenSubKey(RunKey, false))
            {
                if (k == null) return false;
                return k.GetValue(AppName) != null;
            }
        }

        static void SetAutoStart(bool on)
        {
            using (RegistryKey k = Registry.CurrentUser.OpenSubKey(RunKey, true))
            {
                if (k == null) return;
                if (on) k.SetValue(AppName, "\"" + Application.ExecutablePath + "\"");
                else k.DeleteValue(AppName, false);
            }
        }

        protected override void ExitThreadCore()
        {
            if (hook != IntPtr.Zero) Native.UnhookWindowsHookEx(hook);
            if (icon != null) { icon.Visible = false; icon.Dispose(); }
            base.ExitThreadCore();
        }
    }

    static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            Native.SetProcessDPIAware();
            if (args.Length > 0 && args[0] == "--selftest")
            {
                int delay = 420;
                if (args.Length > 1) int.TryParse(args[1], out delay);
                string bg = "screen";
                if (args.Length > 2) bg = args[2];
                RunSelfTest(delay, bg);
                return;
            }
            TrayContext ctx = new TrayContext();
            TrayContext.Current = ctx;
            Application.Run(ctx);
        }

        static void RunSelfTest(int delayMs, string bgMode)
        {
            Rectangle b = Screen.PrimaryScreen.Bounds;
            Point center = new Point(b.Left + b.Width / 2, b.Top + b.Height / 2);
            DropForm f = new DropForm(center, 76, bgMode);
            f.Show();
            DateTime t0 = DateTime.Now;
            while ((DateTime.Now - t0).TotalMilliseconds < delayMs)
            {
                Application.DoEvents();
                System.Threading.Thread.Sleep(8);
            }
            int capSide = 300;
            Rectangle cap = new Rectangle(center.X - capSide / 2, center.Y - capSide / 2, capSide, capSide);
            using (Bitmap bmp = new Bitmap(cap.Width, cap.Height))
            {
                using (Graphics g = Graphics.FromImage(bmp)) g.CopyFromScreen(cap.Location, Point.Empty, cap.Size);
                string outp = Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), "selftest_" + bgMode + "_" + delayMs + ".png");
                bmp.Save(outp, ImageFormat.Png);
            }
            f.Close();
        }
    }
}
