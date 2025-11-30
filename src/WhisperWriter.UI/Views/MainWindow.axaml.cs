using Avalonia.Controls;
using WhisperWriter.UI.ViewModels;

namespace WhisperWriter.UI.Views;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
    }

    public MainWindow(MainViewModel viewModel) : this()
    {
        DataContext = viewModel;
        viewModel.OpenSettingsCommand.Execute(null);
    }
}
