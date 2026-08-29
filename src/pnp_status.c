/*
 * pnp_status.exe - Check PnP device status or get InstanceId by friendly name
 *
 * Usage:
 *   pnp_status.exe "<FriendlyName>" [<Class>]
 *     Returns: "OK", "Unknown", "Disabled", "Error", or "NotFound"
 *   pnp_status.exe --instanceid "<FriendlyName>" [<Class>]
 *     Returns: the InstanceId string, or "NotFound"
 *
 * Default class: AudioEndpoint
 * Uses SetupDi API directly — no PowerShell, minimal memory footprint.
 * Compile: gcc -O2 -o pnp_status.exe pnp_status.c -lsetupapi -lcfgmgr32
 */
#include <windows.h>
#include <setupapi.h>
#include <devguid.h>
#include <cfgmgr32.h>
#include <stdio.h>
#include <string.h>
#include <initguid.h>

/* AudioEndpoint class GUID: {c166523c-fe0c-4a94-a586-f1a80cfbbf3e} */
DEFINE_GUID(GUID_DEVCLASS_AUDIO_ENDPOINT,
    0xc166523c, 0xfe0c, 0x4a94, 0xa5, 0x86, 0xf1, 0xa8, 0x0c, 0xfb, 0xbf, 0x3e);
/* Media class GUID: {4d36e96e-e325-11ce-bfc1-08002be10318} */
DEFINE_GUID(GUID_DEVCLASS_MEDIA,
    0x4d36e96e, 0xe325, 0x11ce, 0xbf, 0xc1, 0x08, 0x00, 0x2b, 0xe1, 0x03, 0x18);
/* Bluetooth class GUID: {e0cbf06c-cd8b-4647-bb8a-263b43f0f974} */
DEFINE_GUID(GUID_DEVCLASS_BLUETOOTH,
    0xe0cbf06c, 0xcd8b, 0x4647, 0xbb, 0x8a, 0x26, 0x3b, 0x43, 0xf0, 0xf9, 0x74);

#ifndef DN_HAS_PROBLEM
#define DN_HAS_PROBLEM 0x40000000
#endif
#ifndef CM_PROB_DISABLED
#define CM_PROB_DISABLED 0x16
#endif

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: pnp_status.exe \"<FriendlyName>\" [<Class>]\n");
        fprintf(stderr, "       pnp_status.exe --instanceid \"<FriendlyName>\" [<Class>]\n");
        return 1;
    }

    int getInstanceId = 0;
    int nameArgIdx = 1;
    if (strcmp(argv[1], "--instanceid") == 0) {
        getInstanceId = 1;
        nameArgIdx = 2;
        if (argc < 3) {
            fprintf(stderr, "Usage: pnp_status.exe --instanceid \"<FriendlyName>\" [<Class>]\n");
            return 1;
        }
    }

    const char *targetName = argv[nameArgIdx];
    const char *className = (argc >= nameArgIdx + 2) ? argv[nameArgIdx + 1] : "AudioEndpoint";

    /* Convert class name to class GUID */
    GUID classGuid;
    if (strcmp(className, "AudioEndpoint") == 0) {
        classGuid = GUID_DEVCLASS_AUDIO_ENDPOINT;
    } else if (strcmp(className, "Bluetooth") == 0) {
        classGuid = GUID_DEVCLASS_BLUETOOTH;
    } else if (strcmp(className, "Media") == 0) {
        classGuid = GUID_DEVCLASS_MEDIA;
    } else {
        /* Try to look it up by name */
        if (!SetupDiClassGuidsFromNameA(className, &classGuid, 1, NULL)) {
            printf("Error\n");
            return 1;
        }
    }

    /* Enumerate devices of this class (present only) */
    HDEVINFO hDevInfo = SetupDiGetClassDevsW(&classGuid, NULL, NULL,
        DIGCF_PRESENT);
    if (hDevInfo == INVALID_HANDLE_VALUE) {
        printf("Error\n");
        return 1;
    }

    /* Also try without DIGCF_PRESENT — disconnected devices aren't "present" */
    HDEVINFO hDevInfoAll = SetupDiGetClassDevsW(&classGuid, NULL, NULL, 0);

    SP_DEVINFO_DATA devInfoData;
    devInfoData.cbSize = sizeof(SP_DEVINFO_DATA);

    /* Check present devices first, then all devices */
    HDEVINFO handles[2] = {hDevInfo, hDevInfoAll};
    DWORD h;
    for (h = 0; h < 2; h++) {
        if (!handles[h] || handles[h] == INVALID_HANDLE_VALUE) continue;

        DWORD i;
        for (i = 0; SetupDiEnumDeviceInfo(handles[h], i, &devInfoData); i++) {
            WCHAR friendlyNameW[512] = {0};
            char friendlyNameA[512] = {0};

            if (SetupDiGetDeviceRegistryPropertyW(handles[h], &devInfoData,
                    SPDRP_FRIENDLYNAME, NULL, (PBYTE)friendlyNameW,
                    sizeof(friendlyNameW) - sizeof(WCHAR), NULL)) {
                WideCharToMultiByte(CP_UTF8, 0, friendlyNameW, -1,
                    friendlyNameA, sizeof(friendlyNameA), NULL, NULL);
                if (_stricmp(friendlyNameA, targetName) == 0) {
                    if (getInstanceId) {
                        WCHAR instanceIdW[512] = {0};
                        char instanceIdA[512] = {0};
                        if (SetupDiGetDeviceInstanceIdW(handles[h], &devInfoData,
                                instanceIdW, sizeof(instanceIdW) / sizeof(WCHAR), NULL)) {
                            WideCharToMultiByte(CP_UTF8, 0, instanceIdW, -1,
                                instanceIdA, sizeof(instanceIdA), NULL, NULL);
                            printf("%s\n", instanceIdA);
                        } else {
                            printf("Error\n");
                        }
                    } else {
                        ULONG status = 0, problem = 0;
                        if (CM_Get_DevNode_Status(&status, &problem,
                                devInfoData.DevInst, 0) == CR_SUCCESS) {
                            if (status == DN_HAS_PROBLEM && problem == CM_PROB_DISABLED) {
                                printf("Disabled\n");
                            } else if (status == 0 || !(status & DN_HAS_PROBLEM)) {
                                printf("OK\n");
                            } else {
                                printf("Unknown\n");
                            }
                        } else {
                            printf("Unknown\n");
                        }
                    }
                    SetupDiDestroyDeviceInfoList(hDevInfo);
                    if (hDevInfoAll && hDevInfoAll != INVALID_HANDLE_VALUE)
                        SetupDiDestroyDeviceInfoList(hDevInfoAll);
                    return 0;
                }
            }
        }
    }

    printf("NotFound\n");
    SetupDiDestroyDeviceInfoList(hDevInfo);
    if (hDevInfoAll && hDevInfoAll != INVALID_HANDLE_VALUE)
        SetupDiDestroyDeviceInfoList(hDevInfoAll);
    return 0;
}
