using Avalonia;
using Avalonia.Controls;
using WhisperWriter.UI.ViewModels;

namespace WhisperWriter.UI.Views;

public partial class StatusWindow : Window
{
    public StatusWindow()
    {
        InitializeComponent();
        PositionWindow();
    }

    public StatusWindow(StatusViewModel viewModel) : this()
    {
        DataContext = viewModel;
    }

    private void PositionWindow()
    {
        // Position in bottom-right corner of primary screen
        var screen = Screens.Primary;
        if (screen != null)
        {
            var workingArea = screen.WorkingArea;
            Position = new PixelPoint(
                workingArea.Right - (int)Width - 20,
                workingArea.Bottom - (int)Height - 20);
        }
    }
}
