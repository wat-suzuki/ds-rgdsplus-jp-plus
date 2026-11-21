#!/usr/bin/env python3
"""Compile regression harnesses from the actual hook functions (no device I/O).

SDL2_CONFIG selects a native SDL2 development installation. XGL checks use GL
stubs to check resource/state handling, not to claim a device GPU result.
"""
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "libhookdrastic.c").read_text()


def section(start, end):
    begin = SOURCE.index(start)
    return SOURCE[begin:SOURCE.index(end, begin)]


def function(signature):
    begin = SOURCE.index(signature)
    opening = SOURCE.index("{", begin)
    depth = 0
    # Skip quoted braces and comments when locating a function's closing brace.
    tokens = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*|[{}]'
    for token in re.finditer(tokens, SOURCE[opening:]):
        if token[0] == "{":
            depth += 1
        elif token[0] == "}":
            depth -= 1
            if not depth:
                return SOURCE[begin:opening + token.end()]
    raise ValueError(signature)


PREAMBLE = r'''
#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include <assert.h>
#include <ctype.h>
#include <dirent.h>
#include <dlfcn.h>
#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include "utf8.h"
#include "xgl.h"
SDL_Surface *IMG_Load(const char *path);
#define SCREEN_WIDTH 1024
#define SCREEN_HEIGHT 768
#define SCREEN_COUNT 2
#define MAX_PATH 512
#define MAX_FILE 256
#define NUMBER_OF(a) (sizeof(a) / sizeof((a)[0]))
#define WHITE_COLOR ((SDL_Color){255,255,255,255})
'''


def font_harness():
    return (PREAMBLE + section("static struct {\n\tchar root[", "static void Paths_init(")
            + section("typedef struct {\n\tint valid;", "// input abstraction")
            + function("static int App_wrap(") + function("static void App_trunc(") + r'''
static int unicode_width(TTF_Font *font, const char *text, int *w, int *h) {
    (void)font; *w = 0;
    while (*text) { unsigned int c = UTF8_next(&text); *w += c < 128 ? 12 : 36; }
    if (h) *h = 36;
    return 0;
}
static void valid_utf8(const char *s) {
    while (*s) {
        size_t n = UTF8_charBytes((const unsigned char *)s);
        assert((unsigned char)*s < 128 || n > 1);
        s += n;
    }
}
int main(void) {
    assert(UTF8_charBytes((const unsigned char *)"あ") == 3);
    assert(UTF8_charBytes((const unsigned char *)"𠮷") == 4);
    const char *bad[] = {"\xc2", "\xe3", "\xe3\x81", "\xf0\x90\x80", "\xed\xa0\x80", "\xc0\x80"};
    for (size_t i = 0; i < NUMBER_OF(bad); i++) {
        char *copy = strdup(bad[i]);
        assert(UTF8_charBytes((const unsigned char *)copy) == 1);
        free(copy);
    }
    assert(compareNatural("ゲーム 2.nds", "ゲーム 10.nds") < 0);
    assert(compareNatural("Game IX.nds", "Game X.nds") < 0);
    assert(compareNatural("Game.nds", "Game 2.nds") < 0);
    assert(compareNatural("あ.nds", "ア.nds") == 0);
    assert(compareNatural("あ.nds", "い.nds") < 0);
    /* Bitmap fallback must consume a whole code point without indexing past 127. */
    int width = 0;
    Font_getTextSize(font36, "日本語𠮷", &width, NULL);
    assert(width > 0);
    font36->ttf = (TTF_Font *)1;
    ttf_size_utf8_fn = unicode_width;
    char name[MAX_FILE] = "";
    for (int i = 0; i < 70; i++) strcat(name, "あ");
    char *lines[8] = {0}; int splits[8] = {0};
    int count = App_wrap(font36, name, 8, lines, splits);
    assert(count == 3);
    char joined[1024] = "";
    for (int i = 0; i < count; i++) {
        valid_utf8(lines[i]);
        Font_getTextSize(font36, lines[i], &width, NULL);
        assert(width <= SCREEN_WIDTH - 40);
        strcat(joined, lines[i]); free(lines[i]);
    }
    assert(strcmp(name, joined) == 0);
    assert(App_wrap(font36, name, 1, lines, splits) == 1); free(lines[0]);
    char shortened[MAX_FILE];
    App_trunc(font36, name, 180, shortened);
    valid_utf8(shortened);
    Font_getTextSize(font36, shortened, &width, NULL);
    assert(width <= 180 && strstr(shortened, "…"));
    puts("UTF-8, kana/numeric ordering, fallback, wrapping and truncation passed");
    return 0;
}
''')


def settings_harness():
    return (PREAMBLE + section("static struct {\n\tchar root[", "static void Paths_init(")
            + "static struct { char game_id[5]; } app;\n"
            + section("typedef enum {\n\tDISPLAY_OFF", "static void Settings_setVolume") + r'''
static void write_file(const char *path, const char *text) {
    FILE *f = fopen(path, "wb"); assert(f); assert(fputs(text, f) >= 0); assert(fclose(f) == 0);
}
static char *read_file(const char *path) {
    static char buffer[8192]; FILE *f = fopen(path, "rb"); assert(f);
    size_t n = fread(buffer, 1, sizeof(buffer) - 1, f); buffer[n] = 0; fclose(f); return buffer;
}
int main(void) {
    char directory[] = "/tmp/dsplus-settings.XXXXXX";
    assert(mkdtemp(directory));
    strcpy(paths.system, directory);
    snprintf(paths.settings, sizeof(paths.settings), "%s/settings.bin", directory);
    char config[MAX_PATH], sub[MAX_PATH];
    mkdir(Path_concat(sub, directory, "/drastic"), 0755);
    mkdir(Path_concat(sub, directory, "/drastic/config"), 0755);
    Path_concat(config, directory, "/drastic/config/drastic.cfg");
    write_file(config, "hires_3d = 0\nscreen_orientation = 1\ncontrols_b[CONTROL_INDEX_SELECT] = 1030\n");
    assert(Config_set_hires_3d(1));
    assert(Config_get_hires_3d() == 1);
    char *text = read_file(config);
    assert(strstr(text, "screen_orientation = 1"));
    assert(strstr(text, "CONTROL_INDEX_SELECT] = 1030"));
    assert(strstr(text, "threaded_3d = 1"));
    strcpy(app.game_id, "AZEJ"); assert(Config_set_hires_3d(1));
    text = read_file(config);
    assert(strstr(text, "threaded_3d = 0") && strstr(text, "frameskip_type = 2"));
    assert(Config_set_hires_3d(0)); assert(Config_get_hires_3d() == 0);
    /* Exact old layout: four reserved ints followed by the original ROM name. */
    struct { int version,volume,brightness,grid,unused[4]; char game[MAX_PATH]; } old = {
        .version=1, .volume=7, .brightness=8, .grid=0, .unused={99,98,97,96}, .game="日本語.nds"
    };
    assert(sizeof(old) == sizeof(settings));
    FILE *f = fopen(paths.settings, "wb"); assert(f);
    assert(fwrite(&old, sizeof(old), 1, f) == 1); fclose(f);
    Settings_load();
    assert(settings.version == 2 && settings.display_mode == DISPLAY_OFF);
    assert(settings.volume == 7 && settings.brightness == 8 && settings.grid == 0);
    assert(strcmp(settings.game, "日本語.nds") == 0);
    settings.display_mode = DISPLAY_HIRES; assert(Settings_save());
    settings.display_mode = DISPLAY_OFF; Settings_load(); assert(settings.display_mode == DISPLAY_OFF);
    char blocked[MAX_PATH]; snprintf(blocked, sizeof(blocked), "%s.tmp", paths.settings);
    assert(mkdir(blocked, 0755) == 0);
    settings.display_mode = DISPLAY_HIRES; assert(!Settings_save());
    settings.display_mode = DISPLAY_OFF; Settings_load(); assert(settings.display_mode == DISPLAY_OFF);
    rmdir(blocked);
    unlink(paths.settings); unlink(config);
    rmdir(Path_concat(sub, directory, "/drastic/config"));
    rmdir(Path_concat(sub, directory, "/drastic")); rmdir(directory);
    puts("Atomic config/settings writes, compatibility exceptions and old-layout migration passed");
    return 0;
}
''')


def mode_harness():
    return (PREAMBLE + r'''
typedef enum { DISPLAY_OFF, DISPLAY_HIRES, DISPLAY_MODE_COUNT } DisplayMode;
static struct { int display_mode; } settings;
static int display_notice_pending, display_notice_active;
static int saved, waited, configured, quit_count, config_value;
static int allow_save=1, allow_settings=1, allow_config=1;
static const char *DisplayMode_label(int m) { const char *a[]={"Off","Hi-Res"}; return a[m]; }
static int App_save(int slot) { assert(slot==0); saved++; return allow_save; }
static void drastic_await_save(void) { waited++; }
static int Config_set_hires_3d(int value) { configured++; config_value=value; return allow_config; }
static int Settings_save(void) { return allow_settings; }
static void drastic_quit(void) { quit_count++; }
#define STATE_AUTO 0
''' + function("static void DisplayMode_cycle(void) {") + r'''
int main(void) {
    DisplayMode_cycle(); assert(settings.display_mode==DISPLAY_HIRES && saved==1 && waited==1 && quit_count==1 && config_value==1);
    DisplayMode_cycle(); assert(settings.display_mode==DISPLAY_OFF && quit_count==2 && config_value==0);
    allow_save=0;
    DisplayMode_cycle(); assert(settings.display_mode==DISPLAY_OFF && quit_count==2);
    allow_save=1; allow_config=0;
    DisplayMode_cycle(); assert(settings.display_mode==DISPLAY_OFF && quit_count==2);
    allow_config=1; allow_settings=0;
    DisplayMode_cycle(); assert(settings.display_mode==DISPLAY_OFF && quit_count==2 && config_value==1);
    puts("Display cycle, save-before-restart and failure rollback passed");
    return 0;
}
''')


def hotkey_harness():
    return (PREAMBLE + section("static struct {\n\tchar root[", "static void Paths_init(")
            + section("#define PAD_REPEAT_TIMEOUT", "static int Pad_fakeButtonEvent(")
            + function("static void Pad_consume(") + r'''
static struct {int menu,capture,screen_swap; char game_name[MAX_FILE];} app;
static struct {int grid,brightness;} settings;
static struct {int state;} loader;
static int idling,power_at,cycles;
#define LOADER_IDLE 0
static void Device_sleep(void) {}
static void Device_idle(void) {}
static int hangs_on_lid(void) {return 0;}
static void DisplayMode_cycle(void) {cycles++;}
''' + function("static inline int exists(") + function("static void State_path(")
            + function("static void ScreenSwap_load(void) {")
            + function("static void ScreenSwap_toggle(void) {")
            + function("static int Device_handleEvent(") + r'''
static void combo(unsigned button) {
    SDL_Event event={0};
    pad.is_pressed=PAD_MENU;pad.just_pressed=PAD_MENU;pad.just_released=0;
    Device_handleEvent(&event);
    pad.is_pressed|=button;pad.just_pressed=button;
    assert(Device_handleEvent(&event)==1 && !Pad_justPressed(button));
    pad.is_pressed=0;pad.just_pressed=0;pad.just_released=PAD_MENU;
    assert(Device_handleEvent(&event)==1 && !Pad_justReleased(PAD_MENU));
}
int main(void) {
    char directory[]="/tmp/dsplus-hotkeys.XXXXXX";assert(mkdtemp(directory));
    strcpy(paths.userdata,directory);char parent[MAX_PATH],path[MAX_PATH];
    mkdir(Path_concat(parent,directory,"/states"),0755);
    strcpy(app.game_name,"日本語ゲーム");ScreenSwap_load();assert(!app.screen_swap);
    combo(PAD_SELECT);assert(cycles==0 && app.screen_swap);
    combo(PAD_START);assert(cycles==1 && !app.capture);
    State_path(path,app.game_name,"screen.swap");assert(exists(path));
    strcpy(app.game_name,"Other");ScreenSwap_load();assert(!app.screen_swap);
    combo(PAD_SELECT);assert(app.screen_swap);
    strcpy(app.game_name,"日本語ゲーム");ScreenSwap_load();assert(app.screen_swap);
    combo(PAD_SELECT);assert(!app.screen_swap);
    strcpy(app.game_name,"Other");ScreenSwap_load();assert(app.screen_swap);
    combo(PAD_A);assert(app.capture && cycles==1);
    SDL_Event event={0};pad.is_pressed=PAD_SELECT;pad.just_pressed=PAD_SELECT;pad.just_released=0;
    assert(Device_handleEvent(&event)==0 && cycles==1);
    app.menu=1;pad.is_pressed=PAD_MENU|PAD_SELECT;pad.just_pressed=PAD_SELECT;
    assert(Device_handleEvent(&event)==0 && cycles==1); /* LOAD+SELECT is preserved. */
    State_path(path,"Other","screen.swap");unlink(path);
    State_path(path,"Other","");rmdir(path);
    State_path(path,"日本語ゲーム","");rmdir(path);rmdir(parent);rmdir(directory);
    puts("MENU+SELECT/MENU+START/MENU+A, release consumption and per-game UTF-8 swap files passed");
    return 0;
}
''')


def audio_harness():
    return (PREAMBLE + '#include "avprobe.h"\n' + r'''
static AVProfile av_profile;
static struct {uintptr_t base;int menu;} app;
static struct {int volume;} settings={7};
static int open_result,original_calls,last_delay;
static SDL_AudioSpec seen;
static void dmesg(const char *s) {(void)s;}
static void raw_audio_init(void) {}
static void raw_vol(int volume) {(void)volume;}
static void Settings_setVolume(int volume) {assert(volume==7);}
static int fake_open(SDL_AudioSpec *desired,SDL_AudioSpec *obtained) {
    seen=*desired;
    if(open_result)return open_result;
    if(obtained){*obtained=*desired;obtained->samples=940;}
    else {desired->size=4096;desired->silence=0;}
    return 0;
}
static void fake_delay(uint32_t ms) {last_delay=ms;}
static int (*real_SDL_OpenAudio)(SDL_AudioSpec *,SDL_AudioSpec *)=fake_open;
static void (*real_SDL_Delay)(uint32_t)=fake_delay;
''' + section("static struct {\n\tvoid (*callback)", "// microphone support") + r'''
#define SDL_OpenAudio Hook_OpenAudio
#define SDL_Delay Hook_Delay
''' + function("int SDL_OpenAudio(") + function("void SDL_Delay(") + r'''
static void original(void *userdata,Uint8 *stream,int size) {
    assert(userdata==&original_calls);original_calls++;memset(stream,0x5a,size);
}
int main(void) {
    SDL_AudioSpec requested={.callback=original,.userdata=&original_calls,.freq=44100,
        .format=AUDIO_S16SYS,.channels=2,.samples=1024},actual;
    AVProfile_init(&av_profile,0);
    assert(Hook_OpenAudio(&requested,&actual)==0 && seen.callback==Audio_callback);
    assert(seen.freq==44100 && seen.samples==1024 && seen.format==AUDIO_S16SYS && seen.channels==2);
    Uint8 output[32];seen.callback(seen.userdata,output,sizeof(output));
    assert(original_calls==1 && output[0]==0x5a);
    app.menu=1;seen.callback(seen.userdata,output,sizeof(output));assert(original_calls==1 && output[0]==0);
    app.menu=0;audio.mute=1;seen.callback(seen.userdata,output,sizeof(output));assert(original_calls==2 && output[0]==0);
    audio.mute=0;AVProfile_init(&av_profile,2);
    assert(Hook_OpenAudio(&requested,&actual)==0 && seen.callback==AVProfile_audioCallback);
    assert(av_profile.callback==Audio_callback && av_profile.audio_frame_bytes==4);
    seen.callback(seen.userdata,output,sizeof(output));assert(original_calls==3 && output[0]==0x5a);
    assert(av_profile.callbacks==1 && !av_profile.ring_probes);
    AVProfile_pauseAudio(&av_profile,1);app.menu=1;
    seen.callback(seen.userdata,output,sizeof(output));assert(av_profile.callbacks==1 && original_calls==3 && output[0]==0);
    app.menu=0;AVProfile_pauseAudio(&av_profile,0);
    seen.callback(seen.userdata,output,sizeof(output));assert(av_profile.callbacks==2 && original_calls==4);
    assert(!av_profile.metrics[AV_AUDIO_GAP].count);
    assert(Hook_OpenAudio(&requested,NULL)==0 && requested.size==4096);
    Hook_Delay(100);assert(last_delay==16);Hook_Delay(0);assert(last_delay==0);
    open_result=-1;assert(Hook_OpenAudio(&requested,&actual)==-1 && !av_profile.callback && !av_profile.ring_read);
    puts("Actual audio hook: profile 0/2, original callback/userdata, menu/FF mute, pause epochs, audio requests and delay clamp passed");
    return 0;
}
''')


def render_harness():
    preamble = PREAMBLE.replace('#include "xgl.h"', r'''
static Uint64 ticks=100;
static int counter_calls;
static Uint64 fake_counter(void) {counter_calls++;return ticks;}
static Uint64 fake_frequency(void) {return 1000000;}
#define SDL_GetPerformanceCounter fake_counter
#define SDL_GetPerformanceFrequency fake_frequency
#include "xgl.h"
#include "avsystem.h"
''')
    return preamble + r'''
typedef enum {DISPLAY_OFF,DISPLAY_HIRES} DisplayMode;
enum {LOADER_IDLE,LOADER_REQUESTED,LOADER_AWAITING,LOADER_STARTED,LOADER_COMPLETE};
enum {LOADER_RESET,LOADER_RESUME};
#define STATE_LATEST -1
static AVProfile av_profile;
static AVSystem av_system;
static struct {
    int menu,screen_swap,capture;char game_path[10];
    struct {XGL_Renderer *renderers[2];XGL_Shader *game_shaders[2];XGL_Texture *screens[2],*grid,*icons;
        int fused_grid_last[2];} xgl;
    struct {struct {Uint64 pixels_started;} screens[2];} dummy;
} app;
static struct {int state,after;} loader;
static struct {int grid,display_mode;} settings;
static struct {int mute;} audio;
static struct {char assets[10];} paths;
static int idling,use_fused_grid=1,use_grouped_present,display_notice_pending,display_notice_active,rendered_first_frame=1;
static Uint32 display_notice_at;
static int grids,swaps,game_draws;
static XGL_Texture *drawn[2];
static char order_trace[256];
static void trace(char c) {size_t n=strlen(order_trace);assert(n+1<sizeof(order_trace));order_trace[n]=c;order_trace[n+1]=0;}
static void *font24;
static const char *DisplayMode_label(int mode) {(void)mode;return "Off";}
static char *Path_concat(char *out,...) {out[0]=0;return out;}
static void OSD_render(XGL_Renderer *renderer) {(void)renderer;}
static void Font_shadowText(XGL_Renderer *renderer,void *font,const char *s,int x,int y,SDL_Color c) {
    (void)renderer;(void)font;(void)s;(void)x;(void)y;(void)c;
}
static void App_grid(XGL_Renderer *renderer) {(void)renderer;grids++;ticks+=20;}
static void App_capture(const char *name) {assert(!strcmp(name,"game"));trace('C');app.capture=0;}
static void dmesg(const char *name) {(void)name;}
static void fake_delay(uint32_t ms) {ticks+=ms*1000;}
static void (*real_SDL_Delay)(uint32_t)=fake_delay;
static void Device_tick(void) {ticks+=10;}
static void Device_mute(int mute) {(void)mute;}
static void App_load(int slot) {(void)slot;}
static void drastic_load_nds_and_jump(const char *path) {(void)path;}
int XGL_SetRenderShader(XGL_Renderer *r,XGL_Shader *s) {(void)r;(void)s;return 0;}
int XGL_SetShaderGrid(XGL_Shader *s,XGL_Texture *t) {(void)t;return s?0:-1;}
int XGL_RenderCopy(XGL_Renderer *r,XGL_Texture *t,const SDL_Rect *a,const SDL_Rect *b) {
    (void)a;(void)b;drawn[(uintptr_t)r-1]=t;trace((uintptr_t)r==1?'T':'B');game_draws++;ticks+=100;return 0;
}
void XGL_RenderPresent(XGL_Renderer *r) {trace((uintptr_t)r==1?'t':'b');swaps++;ticks+=300;}
int XGL_GetTexturePixels(XGL_Texture *t,const void **pixels,int *pitch) {(void)t;(void)pixels;(void)pitch;return -1;}
XGL_Texture *XGL_LoadTexture(XGL_Renderer *r,const char *path) {(void)r;(void)path;return NULL;}
''' + function("static void Profile_suspend(") + function("static void App_render(void) {") + r'''
#define SDL_RenderPresent Hook_RenderPresent
''' + function("void SDL_RenderPresent(") + r'''
int main(void) {
    for(int i=0;i<2;i++){app.xgl.renderers[i]=(XGL_Renderer *)(uintptr_t)(i+1);
        app.xgl.screens[i]=(XGL_Texture *)(uintptr_t)(i+10);app.xgl.game_shaders[i]=(XGL_Shader *)1;}
    app.xgl.grid=(XGL_Texture *)20;settings.grid=1;
    AVProfile_init(&av_profile,0);counter_calls=0;
    Hook_RenderPresent(NULL);assert(!counter_calls && swaps==2 && game_draws==2 && !grids);
    assert(!strcmp(order_trace,"TBtb"));order_trace[0]=0;
    AVProfile_init(&av_profile,2);swaps=game_draws=grids=0;
    Hook_RenderPresent(NULL);
    assert(av_profile.metrics[AV_DRAW].count==1 && av_profile.metrics[AV_DRAW].total==200);
    assert(av_profile.metrics[AV_PRESENT].count==1 && av_profile.metrics[AV_PRESENT].total==600);
    assert(av_profile.metrics[AV_DRAW_TOP].count==1 && av_profile.metrics[AV_DRAW_BOTTOM].count==1);
    assert(app.xgl.fused_grid_last[0] && app.xgl.fused_grid_last[1] && !grids);
    ticks+=1000;app.screen_swap=1;Hook_RenderPresent(NULL);
    assert(drawn[0]==app.xgl.screens[1] && drawn[1]==app.xgl.screens[0]);
    assert(av_profile.metrics[AV_PIPELINE].total==800); /* Draw + swaps, no double counting. */
    use_fused_grid=0;Hook_RenderPresent(NULL);assert(grids==2);
    assert(av_profile.metrics[AV_GRID_TOP].count==1 && av_profile.metrics[AV_GRID_BOTTOM].count==1);
    
    Uint64 draws=av_profile.metrics[AV_DRAW].count;
    idling=1;Hook_RenderPresent(NULL);assert(!av_profile.last_frame && av_profile.audio_paused);
    assert(av_profile.metrics[AV_DRAW].count==draws);
    idling=0;loader.state=LOADER_REQUESTED;Hook_RenderPresent(NULL);
    assert(loader.state==LOADER_AWAITING && !av_profile.last_frame);
    loader.state=LOADER_COMPLETE;Hook_RenderPresent(NULL);assert(loader.state==LOADER_IDLE && !av_profile.last_frame);
    Hook_RenderPresent(NULL);assert(av_profile.last_frame && !av_profile.audio_paused);
    for(int level=0;level<=2;level++) {
        use_grouped_present=1;settings.display_mode=DISPLAY_OFF;
        AVProfile_init(&av_profile,level);counter_calls=0;order_trace[0]=0;
        grids=0;swaps=0;game_draws=0;
        Hook_RenderPresent(NULL);
        assert(!strcmp(order_trace,"TtBb") && swaps==2 && game_draws==2 && grids==2);
        if(!level)assert(!counter_calls);
        else {
            assert(av_profile.metrics[AV_DRAW].count==1 && av_profile.metrics[AV_DRAW].total==240);
            assert(av_profile.metrics[AV_PRESENT].count==1 && av_profile.metrics[AV_PRESENT].total==600);
        }
        order_trace[0]=0;ticks+=1000;
        Hook_RenderPresent(NULL);assert(!strcmp(order_trace,"TtBb"));
        if(level==2) assert(av_profile.metrics[AV_PIPELINE].count==1 && av_profile.metrics[AV_PIPELINE].total==840);
        /* A capture must read BOTH current backbuffers before EITHER swap. */
        order_trace[0]=0;app.capture=1;
        Hook_RenderPresent(NULL);assert(!strcmp(order_trace,"TBCtb") && !app.capture);
    }
    puts("Actual Present/render hooks: disabled clocks, separate draw/swap totals, fused/fallback grid, swapped screens and load/sleep reset passed");
    puts("Batched/grouped order, one draw/present sample per frame, disjoint pipeline union and capture fallback passed");
    return 0;
}
'''


def xgl_harness(prefix):
    source = (ROOT / "xgl.c").read_text()
    header = (Path(prefix) / "include/SDL2/SDL_opengles2_gl2.h").read_text()
    bodies = {
        "glGenTextures": "for(int i=0;i<n;i++){textures[i]=++next_id;live_textures++;}",
        "glDeleteTextures": "live_textures-=n;",
        "glGenBuffers": "for(int i=0;i<n;i++)buffers[i]=++next_id;",
        "glGenFramebuffers": "for(int i=0;i<n;i++){framebuffers[i]=++next_id;live_fbos++;}",
        "glDeleteFramebuffers": "live_fbos-=n;",
        "glCreateShader": "return ++next_id;",
        "glCreateProgram": "return ++next_id;",
        "glGetAttribLocation": "return strcmp(name,\"a_position\")==0 ? 0 : 1;",
        "glGetUniformLocation": 'if(!strcmp(name,"u_grid_enabled"))return 50;if(!strcmp(name,"u_grid"))return 51;if(!strcmp(name,"u_grid_size"))return 52;if(!strcmp(name,"u_grid_height"))return 53;if(!strcmp(name,"u_grid_color"))return 54;return 1;',
        "glGetShaderiv": "*params=1;",
        "glGetProgramiv": "*params=1;",
        "glCheckFramebufferStatus": "return fail_fbo ? GL_FRAMEBUFFER_UNSUPPORTED : GL_FRAMEBUFFER_COMPLETE;",
        "glBindFramebuffer": "bound_fbo=framebuffer;",
        "glActiveTexture": "active_texture=texture;",
        "glBindTexture": "if(active_texture==GL_TEXTURE1)bound_grid=texture;else bound_texture=texture;",
        "glUniform1i": "if(location==50)grid_enabled=v0;",
        "glUniform1f": "if(location==53)grid_height=v0;",
        "glGetIntegerv": "if(pname==GL_FRAMEBUFFER_BINDING)*data=bound_fbo;else if(pname==GL_VIEWPORT)memcpy(data,viewport,sizeof(viewport));else *data=0;",
        "glViewport": "viewport[0]=x;viewport[1]=y;viewport[2]=width;viewport[3]=height;",
        "glBufferData": "assert(size==sizeof(quad));memcpy(quad,data,sizeof(quad));",
        "glDrawArrays": "assert(draws<16);grid_flags[draws]=grid_enabled;frames[draws]=bound_fbo;draw_textures[draws]=bound_texture;memcpy(vertices[draws],quad,sizeof(quad));memcpy(viewports[draws],viewport,sizeof(viewport));draws++;",
        "glTexSubImage2D": "uploads++;",
        "glTexParameteri": "if(pname==GL_TEXTURE_MIN_FILTER||pname==GL_TEXTURE_MAG_FILTER)filter_calls++;",
    }
    definitions = []
    for name in sorted(set(re.findall(r"\b(gl[A-Z]\w+)\s*\(", source))):
        match = re.search(r"GL_APICALL\s+(.+?)\s+GL_APIENTRY\s+" + name + r"\s*\(([^;]*)\);", header)
        if not match:
            raise ValueError(f"Missing GL prototype: {name}")
        result, args = match.groups()
        body = bodies.get(name, "" if result == "void" else "return 0;")
        definitions.append(f"{result} GL_APIENTRY {name}({args}) {{{body}}}\n")
    hooks = section("typedef struct {\n\tXGL_Texture *texture;", "typedef struct {\n\tSDL_Window *window;")
    hooks += r'''
#define DS_WIDTH 256
#define DS_HEIGHT 192
static struct {
    struct {XGL_Renderer *renderers[2];XGL_Texture *screens[2];XGL_Shader *game_shaders[2];} xgl;
    struct {DummyTexture screens[2],ignored;} dummy;
} app;
static AVProfile av_profile;
#define SDL_CreateTexture Hook_CreateTexture
#define SDL_LockTexture Hook_LockTexture
#define SDL_UnlockTexture Hook_UnlockTexture
#define SDL_UpdateTexture Hook_UpdateTexture
#define SDL_DestroyTexture Hook_DestroyTexture
'''
    for signature in ("SDL_Texture *SDL_CreateTexture(", "static void Game_makeOpaque(",
                      "int SDL_LockTexture(", "void SDL_UnlockTexture(", "int SDL_UpdateTexture(",
                      "void SDL_DestroyTexture(", "static void State_screenshot("):
        hooks += function(signature) + "\n"
    hooks += section("static const char *game_vertex_shader", "static void App_init(void) {")
    return PREAMBLE + r'''
#define SDL_USE_BUILTIN_OPENGL_DEFINITIONS
#include <SDL2/SDL_opengles2.h>
static GLuint next_id, bound_fbo=37, bound_texture,bound_grid;
static GLenum active_texture=GL_TEXTURE0;
static int grid_enabled,grid_flags[16],swaps;
static float grid_height;
static int live_textures, live_fbos, uploads, filter_calls, fail_fbo, draws, make_current_calls;
static GLint viewport[4]={0,0,1024,768}, viewports[16][4];
static GLuint frames[16],draw_textures[16];
static GLfloat quad[24],vertices[16][24];
static SDL_GLContext current_context;
static SDL_Window *current_window;
static int fake_current(SDL_Window *window, SDL_GLContext context) {
    make_current_calls++; current_window=window; current_context=context; return 0;
}
static SDL_GLContext fake_get_context(void) {return current_context;}
static SDL_Window *fake_get_window(void) {return current_window;}
static void fake_drawable(SDL_Window *window,int *w,int *h) {(void)window;*w=1024;*h=768;}
static void fake_swap(SDL_Window *window) {(void)window;swaps++;}
#define SDL_GL_MakeCurrent fake_current
#define SDL_GL_GetCurrentContext fake_get_context
#define SDL_GL_GetCurrentWindow fake_get_window
#define SDL_GL_GetDrawableSize fake_drawable
#define SDL_GL_SwapWindow fake_swap
#include "xgl.c"
''' + "".join(definitions) + hooks + r'''
int main(void) {
    XGL_Renderer *renderer=XGL_CreateRenderer((SDL_Window *)1,(SDL_GLContext)1);
    assert(renderer);
    XGL_Texture *texture=XGL_CreateTexture(renderer,SDL_PIXELFORMAT_ARGB8888,XGL_TEXTUREACCESS_STREAMING,2,2);
    assert(texture);
    const void *image; int pitch; void *pixels;
    assert(XGL_GetTexturePixels(texture,&image,&pitch)!=0);
    assert(XGL_LockTexture(texture,NULL,&pixels,&pitch)==0 && pitch==8);
    assert(XGL_GetTexturePixels(texture,&image,&pitch)!=0);
    const Uint32 colors[4]={0x00112233,0x00445566,0x00778899,0x00aabbcc};
    memcpy(pixels,colors,sizeof(colors));
    XGL_UnlockTexture(texture); assert(uploads==1);
    assert(XGL_GetTexturePixels(texture,&image,&pitch)==0 && memcmp(image,colors,sizeof(colors))==0);
    assert(uploads==1); /* Snapshot access must not upload again. */
    SDL_Surface *view=SDL_CreateRGBSurfaceWithFormatFrom((void *)image,2,2,32,pitch,SDL_PIXELFORMAT_ARGB8888);
    SDL_SetSurfaceBlendMode(view,SDL_BLENDMODE_NONE);
    SDL_Surface *rgb=SDL_ConvertSurfaceFormat(view,SDL_PIXELFORMAT_RGB24,0); assert(rgb);
    const Uint8 *rgb_pixels=rgb->pixels;
    assert(rgb_pixels[0]==0x11 && rgb_pixels[1]==0x22 && rgb_pixels[2]==0x33);
    SDL_FreeSurface(rgb);SDL_FreeSurface(view);
    SDL_Rect part={1,1,1,1};
    assert(XGL_LockTexture(texture,&part,&pixels,&pitch)==0);
    *(Uint32 *)pixels=0x12345678; XGL_UnlockTexture(texture);
    assert(XGL_GetTexturePixels(texture,&image,&pitch)==0);
    assert(((const Uint32 *)image)[0]==colors[0] && ((const Uint32 *)image)[3]==0x12345678);
    part=(SDL_Rect){2,0,1,1}; assert(XGL_LockTexture(texture,&part,&pixels,&pitch)!=0);
    const Uint32 padded[6]={1,2,0xdeadbeef,3,4,0xdeadbeef};
    assert(XGL_UpdateTexture(texture,NULL,padded,12)==0);
    assert(XGL_GetTexturePixels(texture,&image,&pitch)==0);
    assert(((const Uint32 *)image)[0]==1 && ((const Uint32 *)image)[2]==3);
    assert(padded[2]==0xdeadbeef);
    draws=0;
    XGL_Texture *grid=XGL_CreateTexture(renderer,SDL_PIXELFORMAT_ABGR8888,XGL_TEXTUREACCESS_STATIC,4,4);
    assert(grid && XGL_SetTextureBlendMode(grid,SDL_BLENDMODE_BLEND)==0);
    XGL_Shader *game=XGL_CreateShader(renderer,game_vertex_shader,game_fragment_shader);assert(game);
    assert(XGL_SetShaderGrid(game,grid)==0 && XGL_SetRenderShader(renderer,game)==0);
    draws=0;
    assert(XGL_RenderCopy(renderer,texture,NULL,NULL)==0 && draws==1 && grid_flags[0]);
    assert(bound_grid==grid->id && active_texture==GL_TEXTURE0 && grid_height==768);
    draws=0;
    XGL_SetShaderGrid(game,NULL);XGL_SetRenderShader(renderer,NULL);
    assert(XGL_RenderRepeat(renderer,grid,NULL)==0 && !grid_flags[2] && !grid->repeat);
    XGL_DestroyShader(game);XGL_DestroyTexture(grid);
    XGL_DestroyTexture(texture); XGL_DestroyRenderer(renderer);
    assert(live_textures==0 && live_fbos==0);
    app.xgl.renderers[0]=XGL_CreateRenderer((SDL_Window *)1,(SDL_GLContext)1);
    app.xgl.renderers[1]=XGL_CreateRenderer((SDL_Window *)2,(SDL_GLContext)2);
    for(int round=0;round<3;round++) {
        int w=round==1?512:256,h=round==1?384:192;
        SDL_Texture *handles[2];
        for(int i=0;i<2;i++) {
            handles[i]=Hook_CreateTexture(NULL,SDL_PIXELFORMAT_ARGB8888,SDL_TEXTUREACCESS_STREAMING,w,h);
            assert(handles[i]);
            assert(Hook_LockTexture(handles[i],NULL,&pixels,&pitch)==0 && pitch==w*4);
            *(Uint32 *)pixels=0x00112233;
            Hook_UnlockTexture(handles[i]);
            assert(XGL_GetTexturePixels(app.xgl.screens[i],&image,&pitch)==0);
            assert(*(const Uint32 *)image==0xff112233); /* Shader-failure fallback. */
            const Uint32 input=0x00123456;part=(SDL_Rect){1,1,1,1};
            assert(Hook_UpdateTexture(handles[i],&part,&input,4)==0 && input==0x00123456);
            assert(XGL_GetTexturePixels(app.xgl.screens[i],&image,&pitch)==0);
            assert(((const Uint32 *)((const Uint8 *)image+pitch))[1]==0xff123456);
        }
        int before_snapshot=uploads;
        char name[]="/tmp/dsplus-snapshot.XXXXXX";int fd=mkstemp(name);assert(fd>=0);close(fd);
        State_screenshot(0,name);assert(uploads==before_snapshot);
        SDL_Surface *snapshot=SDL_LoadBMP(name);assert(snapshot);
        assert(snapshot->w==w && snapshot->h==h && snapshot->format->BytesPerPixel==3);
        SDL_FreeSurface(snapshot);unlink(name);
        for(int i=0;i<2;i++)Hook_DestroyTexture(handles[i]);
    }
    draws=0;fake_current((SDL_Window *)2,(SDL_GLContext)2);
    int previous_currents=make_current_calls;
    XGL_RenderCopy(app.xgl.renderers[0],app.xgl.screens[1],NULL,NULL);
    XGL_RenderCopy(app.xgl.renderers[1],app.xgl.screens[0],NULL,NULL);
    XGL_RenderPresent(app.xgl.renderers[0]);XGL_RenderPresent(app.xgl.renderers[1]);
    assert(make_current_calls-previous_currents==4);
    draws=0;fake_current((SDL_Window *)2,(SDL_GLContext)2);previous_currents=make_current_calls;
    XGL_RenderCopy(app.xgl.renderers[0],app.xgl.screens[1],NULL,NULL);XGL_RenderPresent(app.xgl.renderers[0]);
    XGL_RenderCopy(app.xgl.renderers[1],app.xgl.screens[0],NULL,NULL);XGL_RenderPresent(app.xgl.renderers[1]);
    assert(make_current_calls-previous_currents==2);
    swaps=0;
    for(int i=0;i<2;i++){XGL_DestroyTexture(app.xgl.screens[i]);XGL_DestroyRenderer(app.xgl.renderers[i]);}
    assert(live_textures==0 && live_fbos==0);
    AVProfile_init(&av_profile,2);XGL_SetProfile(&av_profile);
    renderer=XGL_CreateRenderer((SDL_Window *)1,(SDL_GLContext)1);assert(renderer);
    XGL_SetProfileScreen(renderer,0);
    texture=XGL_CreateTexture(renderer,SDL_PIXELFORMAT_ARGB8888,XGL_TEXTUREACCESS_STREAMING,2,2);
    XGL_SetTextureProfileScreen(texture,0);
    AVProfile_frame(&av_profile);
    assert(XGL_UpdateTexture(texture,NULL,colors,8)==0);
    assert(av_profile.metrics[AV_UPLOAD].count==1 && av_profile.metrics[AV_UPLOAD_TOP].count==1);
    assert(!av_profile.metrics[AV_UPLOAD_BOTTOM].count);
    XGL_RenderPresent(renderer);assert(swaps==1 && av_profile.metrics[AV_SWAP_TOP].count==1);
    fake_current((SDL_Window *)2,(SDL_GLContext)2);
    draws=0;XGL_RenderCopy(renderer,texture,NULL,NULL);
    assert(av_profile.metrics[AV_CONTEXT].count==1 && av_profile.metrics[AV_CONTEXT_TOP].count==1);
    AVProfile_resetFrame(&av_profile);
    XGL_UpdateTexture(texture,NULL,colors,8);XGL_RenderPresent(renderer);
    assert(av_profile.metrics[AV_UPLOAD].count==1 && av_profile.metrics[AV_SWAP_TOP].count==1);
    XGL_SetProfile(NULL);XGL_DestroyTexture(texture);XGL_DestroyRenderer(renderer);
    assert(live_textures==0 && live_fbos==0);
    puts("XGL CPU images, partial updates, RGB snapshots, cache and cleanup passed (GL stubs)");
    puts("Actual game texture hooks: 2 screens, native/Hi-Res recreation, alpha fallback and BMP saves passed");
    puts("Grid fusion final-pass-only binding and per-screen upload/swap/context profiling passed");
    return 0;
}
'''


def main():
    config = os.environ.get("SDL2_CONFIG", "sdl2-config")
    flags = shlex.split(subprocess.check_output([config, "--cflags"], text=True))
    # Include the parent as sources use <SDL2/SDL.h>, not <SDL.h>.
    prefix = subprocess.check_output([config, "--prefix"], text=True).strip()
    flags += [f"-I{prefix}/include", f"-I{ROOT}"]
    libs = shlex.split(subprocess.check_output([config, "--static-libs"], text=True))
    compiler = shlex.split(os.environ.get("CC", "cc"))
    with tempfile.TemporaryDirectory(prefix="dsplus-tests-") as directory:
        cases = [("fonts", font_harness()), ("settings", settings_harness()),
                 ("modes", mode_harness()), ("hotkeys", hotkey_harness()),
                 ("audio_hooks", audio_harness()), ("render_hooks", render_harness()),
                 ("xgl", xgl_harness(prefix))]
        for name in ("avprofile", "avprofile_detail", "avsystem", "avprobe"):
            harness = (ROOT / "tests" / f"test_{name}.c").read_text()
            harness = harness.replace('#include "../', '#include "')
            cases.append((name, harness))
        for name, harness in cases:
            path = Path(directory) / f"test_{name}.c"
            path.write_text(harness)
            binary = path.with_suffix("")
            subprocess.run(compiler + ["-std=gnu11", "-O1", "-g", "-fsanitize=address,undefined",
                "-fno-omit-frame-pointer", "-Wno-deprecated-declarations"] + flags + [str(path), "-o", str(binary)] + libs, check=True)
            subprocess.run([str(binary)], check=True)
    subprocess.run([sys.executable, str(ROOT / "tests/test_launcher.py")], check=True)


if __name__ == "__main__":
    main()
