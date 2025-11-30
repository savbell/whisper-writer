using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Markup.Xaml;
using Microsoft.Extensions.DependencyInjection;
using WhisperWriter.Application.Services;
using WhisperWriter.Core.Interfaces;
using WhisperWriter.UI.ViewModels;
using WhisperWriter.UI.Views;

namespace WhisperWriter;

public class App : Avalonia.Application
{
    private WhisperWriterService? _whisperService;
    private StatusWindow? _statusWindow;

    public override void Initialize()
    {
        AvaloniaXamlLoader.Load(this);
    }

    public override async void OnFrameworkInitializationCompleted()
    {
        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop && Program.ServiceProvider != null)
        {
            // Get services
            _whisperService = Program.ServiceProvider.GetRequiredService<WhisperWriterService>();
            var configService = Program.ServiceProvider.GetRequiredService<IConfigurationService>();
            var audioRecorder = Program.ServiceProvider.GetRequiredService<IAudioRecorderService>();

            // Initialize the service
            await _whisperService.InitializeAsync();

            // Create view models
            var mainViewModel = new MainViewModel(_whisperService);
            var settingsViewModel = new SettingsViewModel(configService, audioRecorder);
            var statusViewModel = new StatusViewModel(_whisperService);

            // Create main window
            var mainWindow = new MainWindow
            {
                DataContext = mainViewModel
            };

            // Set up settings command
            mainViewModel.OpenSettingsCommand = new CommunityToolkit.Mvvm.Input.RelayCommand(() =>
            {
                var settingsWindow = new SettingsWindow(settingsViewModel)
                {
                    // Recreate view model to get fresh config
                    DataContext = new SettingsViewModel(configService, audioRecorder)
                };
                settingsWindow.ShowDialog(mainWindow);
            });

            // Create status window if not hidden
            if (!configService.Configuration.Misc.HideStatusWindow)
            {
                _statusWindow = new StatusWindow(statusViewModel);
                _statusWindow.Show();
            }

            desktop.MainWindow = mainWindow;

            // Start the service
            _whisperService.Start();

            // Handle shutdown
            desktop.ShutdownRequested += OnShutdownRequested;

            // Start minimized if configured
            if (configService.Configuration.Misc.StartMinimized)
            {
                mainWindow.WindowState = Avalonia.Controls.WindowState.Minimized;
            }
        }

        base.OnFrameworkInitializationCompleted();
    }

    private void OnShutdownRequested(object? sender, ShutdownRequestedEventArgs e)
    {
        _whisperService?.Stop();
        _statusWindow?.Close();
    }
}
