# DSplusのAV／XGL計測

SDカード直下の`main.sh`、`system/run.sh`、再ビルドした
`system/lib/libhookdrastic.so`を更新する。`system.zip`内だけの更新では、
SDカード直下の`main.sh`は更新されない。

## 設定と保存先

更新後の`main.sh`は、未指定時に`DRASTIC_PROFILE=0`、
`DRASTIC_PRESENT_ORDER=batched`、`DRASTIC_DRM_OVERLAY=1`を使う。
親シェルから指定した値は維持する。

- `0`: 計測無効。追加の計測時計・CPU時計・`/proc`読み出しを行わない。
- `1`: フレーム間隔、転送、描画、Present、音声の基本計測。
- `2`: CPU／非CPU時間、画面別の転送・描画・グリッド・Swap、GLコンテキスト
  切り替え、入力・Device_tick・SDL_Delay、LinuxのスレッドAffinity・CPU各コア／devfreqの
  周波数・温度、DRMのconnector／CRTC／plane能力を追加。

起動ごとに`userdata/logs/drastic-YYYYMMDD-HHMMSS-PID.log`へ標準出力と
標準エラーを保存する。名前が衝突した場合は連番を付け、以前のログは上書きしない。
保存先を作成・書き込みできない場合は従来の`/tmp/drastic.txt`へ戻る。
`/tmp/drastic-log-path`は最新の保存先を示す補助ファイルで、`make log`もこれを使う。

計測時は冒頭の`Launcher: ... DRASTIC_PROFILE=1`または`2`と、
`AV detail: enabled; schema=dsplus-xgl-2`を確認する。
各画面の出力寸法、要求／実際のswap interval、GL vendor／renderer、
音声の要求／取得後の周波数・形式・チャンネル・samplesも記録する。Linux情報では
スレッドごとの`Cpus_allowed_list`、CPU各コアの周波数とgovernor、`/sys/class/devfreq`
にあるデバイスの現在・最小・最大周波数とgovernorを記録する。
DRM調査はconnector／CRTCの現行または利用可能mode、planeのCRTC適用先・fourcc形式・
幅範囲、atomic／PRIME機能とmodifier情報の有無を記録する。profile 2ではテスト用の
XRGB dumb bufferで両overlay planeの2倍拡大をatomic TEST_ONLY検証する。TEST_ONLYは
表示状態を変更しない。

## 指標の範囲

すべてCPUから観測した経過時間であり、GPU自身の実行時間ではない。
`glFinish`や毎フレームのGPU読み戻しは計測のために追加していない。

| 指標 | 範囲 |
|---|---|
| `frame_interval` | ゲームのPresentフック入口間隔。DS内部の進行速度そのものではない |
| `frame_cpu`／`frame_offcpu` | その間のメインスレッドCPU実行時間／残り。待機や実行順待ち等を含む |
| `outside_present`とCPU／offcpu | 前回Presentフックの戻り直前から今回入口まで。DraStic画像生成・コピー・Unlock転送等を含む |
| `game_pixels` | ゲーム画像のLock成功後からUnlock入口まで。1画面単位 |
| `prepare` | SDL_UpdateTexture経由の入力を保持CPU画像へコピーする時間。game_pixelsと区別する |
| `alpha` | ゲーム用CPUアルファ補正。通常の不透明シェーダ経路では補正を省略するのでほぼ0 |
| `upload` | ゲーム画像のXGL_UpdateTexture全体。コンテキスト切り替え、必要な行詰め、GL転送、CPU保持画像更新を含む。1画面単位 |
| `upload_top`／`upload_bottom` | 上記のDS論理上画面／下画面ごとの時間 |
| `upload_copy` | XGL内の必要な行詰め・CPU保持画像更新のコピー。uploadの内数。全画面Lock/Unlockでは通常不要 |
| `draw` | 2画面のゲーム・グリッド・OSD描画時間の合計。Swapを含めず、1フレームにつき1サンプル |
| `draw_top`／`draw_bottom` | 各物理画面のゲーム描画。融合したグリッドを含み、別パスのグリッド・OSDは含まない |
| `grid_top`／`grid_bottom` | 従来方式の独立したグリッド描画。融合時は別パスがないため計測行も出ない |
| `overlay` | モード通知、音量・明るさOSD、早送りアイコン等。drawの内数 |
| `present` | 2画面のXGL_RenderPresent時間の合計。必要なコンテキスト切り替えとSwapを含み、1フレームにつき1サンプル |
| `swap_top`／`swap_bottom` | 各物理画面のSDL_GL_SwapWindowだけ。presentの内数 |
| `make_current`と画面別項目 | 実際にSDL_GL_MakeCurrentを呼んだ回数・時間。同じコンテキストの場合は呼ばず、数えない |
| `input`／`device_tick` | SDL_PollEventフック／Present後のデバイス処理 |
| `sdl_delay` | ゲームがSDL_Delayへ入って戻るまでの実時間。要求0msも含む |
| `profile_io` | 前回の5秒集計ログ・Linux情報取得の時間。次の集計へ現れる |
| `screen_pipeline_per_frame` | 同じフレーム間隔に含まれる画像準備・画素書き込み・転送・描画・Present・コンテキスト切り替えの区間の和集合 |
| `outside_pipeline_per_frame` | フレーム間隔から上記を引いた時間。内部3DのCPU時間と同義ではない |

**入れ子の指標を単純合計しない。** 例えばuploadの中のmake_currentや、
presentの中のswapを足すと二重に数える。pipelineは区間を結合して重複を除く。
schema=dsplus-xgl-2では、drawとpresentをそれぞれ実際の処理区間の合計として
記録する。grouped方式で間に挟まるSwapの待ち時間をdrawへ含めない。
上位の集計と画面別集計の計測時計は別々に取得するため、微小な差がある。
以前のDSplusでApp_render全体をdrawとしていたログとは範囲が異なる。
draw単独の減少を速度改善とは扱わず、frame_intervalとpresent／swapも確認する。

CPU時計が取得できない場合や、計測中にメインスレッドが変わった場合は
架空のCPU時間を作らず、unavailableやthread_switchesとして表示する。
メニュー・ロード・スリープ中はフレーム連続計測をリセットし、その間の音声不足と
長いコールバック間隔を集計から外す。通常のミュート処理はそのまま実行する。
5秒窓自体は連続した実時間なので、中断を挟んだ最初の集計は比較から除外する。

## 内部3DのCPUサンプリング

AV profileの`AV system: thread`行はスレッド単位のCPU時間で、関数内訳は示さない。
内部3Dの補間・ラスタライズ・ユーザーモードGPUドライバの比率は、実機で全スレッドを
サンプリングして調べる。同梱`system/drastic/drastic`はAArch64 ELFでdebug_infoを含むため、
この実行ファイルと同じBuild IDのデバッグ情報を使えば関数・行へ対応づけられる。

ゲームを比較したいステートまで進め、同じ場面を30～40秒表示してからSSH等の別シェルで
プロセス全体を採取する。`PID`には`pidof drastic`の結果を指定する。

```sh
PID=$(pidof drastic)
perf record -e cpu-clock -F 99 --call-graph dwarf,8192 -p "$PID" -o /mnt/sdcard/userdata/logs/drastic-cpu.data
```

約30秒後にCtrl-Cで採取を終了し、次のレポートを保存する。

```sh
perf report --stdio --children --sort pid,tid,comm,dso,symbol \
  -i /mnt/sdcard/userdata/logs/drastic-cpu.data \
  > /mnt/sdcard/userdata/logs/drastic-cpu.txt
```

`perf`がない、またはカーネル設定で採取を拒否された場合は、そのエラーと
`perf version`を記録する。レポートではメインと各TIDを分け、
`render_polygon_interpolate_*`／`drastic_interpolate_uv_linear`を補間、
`render_polygon_setup_spans_*`・`render_polygon_flush_*`・`render_polygon_*`を
ラスタライズ側、`libGLES`／`libmali`等をユーザーモードドライバ側として集計する。
カーネル内の処理や待ち時間はCPUサンプルだけでは内訳にできないため、必要なら別に
`perf sched timehist`で実行待ちを調べる。30～40秒の採取を同じ場面・Hi-Res設定で行い、
BGRAとRGBAの比較では転送形式だけを切り替える。補間関数がCPUサンプルの大きな割合を
占めると確認できた場合に限り、NEON化候補として検討する。

## 音声とSDL_Delay

リングバッファは、**ミュート用・計測用ラッパーを取り付ける前のDraStic本来の
コールバック**の位置・命令と音声形式を照合した場合だけ参照する。
無効時は`ring_probe=disabled reason=...`を出し、未知の私有メモリを読まない。

- `ring_probes=0`なら、`missing_s16=0`から不足なしとは判断できない。
- `ring_short`はコールバック入口で内部リングのサンプル不足を観測した回数。
  実際の無音挿入回数やALSAのxrun回数ではない。
- `missing_s16`は不足した16bitサンプル数。ステレオ1フレームは2サンプル。
- `late_callbacks`は、その呼び出しが要求する音声時間の1.5倍を超える開始間隔。
- 例えば44.1kHz・1024フレームなら、約23.22msのaudio_gapは正常な周期。

音声コールバックにファイルI/O、ログ、メモリ確保、追加ロック、CPU時計取得を
追加しない。音声周波数・samplesの強制変更やリサンプリングも行わない。

SDL_Delayの呼び出し元は、同梱版の命令も一致した場合だけ
`audio_sync`、`frame_pacing`、`system_frame_sync_late`、
`system_frame_sync_wait`と分類する。未知の版はunclassifiedとなる。
既存の最大16ms制限は維持する。

## 改善と比較手順

### エミュレーション本体と表示経路の切り分け

Hi-Resと`threaded_3d`を維持したまま表示経路を止めるには、SDカード直下の
`main.sh`で次を一時指定する。

```sh
export DRASTIC_PROFILE=2
export DRASTIC_NO_PRESENT=1
```

この診断はゲーム画面のGPU転送・描画・Swapと`SDL_UpdateTexture`の画素コピーを省き、
エミュレーション、CPU上のゲーム画素生成、入力・音声・Device_tickは続ける。
ゲーム画像バッファへのCPU書き込み自体は残る。ログのLauncher行と
`AV display:`で`DRASTIC_NO_PRESENT=1`／`no_present=1`を確認する。
比較では`frame_interval`、`frame_cpu`、`outside_present`、`ring_short`、
`missing_s16`を通常表示時と照らし合わせる。`upload`・`draw`・`present`が
0件またはほぼ0になることも確認する。Hi-Res／threaded設定、ゲーム、ステート、場面、
電源条件を揃え、起動後最初の5秒を除いて30～40秒測る。

表示を止めたときに十分な余裕をもって16.67ms以下となり、音声不足も改善するなら、
表示経路の再設計を優先する。16.67msを超えたままなら内部処理や実行条件を優先する。
この比較は表示処理を丸ごと省く診断であり、CPU書き込みやフレーム同期、OS負荷は残る。
したがって結果は本体／表示の切り分け材料であって、各々の単独実行時間の厳密な合計ではない。
計測後は`DRASTIC_NO_PRESENT`を外して通常表示へ戻す。

### DRM overlayの実出力実験

XGL描画と比較する場合は、`DRASTIC_DRM_OVERLAY=1`を指定する。SDL KMSDRMのDRM FDで
XR24 Dumb Bufferを2画面分確保し、ゲーム画素をコピーして両Overlay Planeを
`DRM_MODE_ATOMIC_NONBLOCK`で更新する。`AV profile: upload`はCPUコピー、`present`はAtomic
Commitの所要時間、`drm_busy_skips`は非同期Commitが`EBUSY`となり、そのフレームの更新を
スキップした回数を示す。音声への影響を避けるため、同期再試行やDRMイベント待ちは行わない。

グリッド、OSD、ショートカット通知、キャプチャ、メニューの表示中はOverlay Planeを外して
XGLへ戻す。初期化やCommitに失敗した場合もXGL出力へフォールバックする。planeのスケーリング
品質はドライバ依存のため、画面表示と上下画面入れ替えを実機で確認する。

### 共有GLコンテキストで2画面を描画する比較

2つのKMSDRMウィンドウと2回のSwapを保ったまま、GLコンテキストだけ共有する比較は
`DRASTIC_SHARED_CONTEXT=1`で行う。通常の個別コンテキストは未指定にする。
両設定で同じHi-Res場面を測り、`make_current`の回数・時間、`present`・各Swap、
`frame_interval`を比べる。ログに`Screen 1: GL context=shared surface`が出ることを確認する。
この試験はコンテキスト切り替えの影響を調べるもので、Swap回数は減らさない。
よってSwap待ちが主な時間なら、単一コンテキストだけで大幅に短縮するとは限らない。

各画面は別の1024×768 drawableとして生成しているため、単一の2048×768 EGL surfaceへ
置き換える方法は、KMSDRMがそのサイズの仮想出力を提供するか確認してから試す。
2つのDSI connectorを1つの論理画面へ束ねる場合は、KMSの複数CRTCを同一atomic commitで
更新できるか、Nearest相当のスケーリングを保てるかが先に必要となる。DRM plane直描画は
DMA-BUF形式・modifier・scale範囲・plane/CRTC対応を実機の`drmMode`情報で確認してから
設計する。現行コードはconnectorのDPMS操作しか行わず、これらの機能は使っていない。

### グリッドOFFでも遅い場合の描画順序比較

提供されたHi-Resの安定区間では、フレーム間隔が約18.4～18.8ms、
2画面のpresentが約5.0～5.1ms、uploadが1画面あたり約1.2msだった。
両方のログが`grid=0 fused_top=0 fused_bottom=0`だったため、グリッド統合の
比較にはなっていない。グリッドOFF時の速度不足を統合で改善することもできない。
swap intervalも既に両画面で0なので、0の再指定による改善は期待できない。
present内の待ちはEGL／KMS／GPU／ドライバ等によるもので、この計測だけで
GPU実行時間と断定はできない。

既定の`batched`は「上描画→下描画→上Swap→下Swap」。
試験用の`grouped`は「上描画→上Swap→下描画→下Swap」とし、この区間の
コンテキスト切り替えを2回減らす。ただし、上Swapの待ちで下画面の描画開始が
遅くなる可能性もあり、presentの約5msを解消できると確認したものではない。

SDカード直下の`main.sh`で、`system/loop.sh`を呼ぶ前に指定する。

```sh
export DRASTIC_PROFILE=2
export DRASTIC_PRESENT_ORDER=grouped
```

G＋L2でグリッド自体をOFFにし、`AV display:`の`grid=0`と
`render_order=grouped`を確認する。同じゲーム・同じステートから同じ場面を
30～40秒測り、起動直後の最初の5秒は除外する。次に
`DRASTIC_PRESENT_ORDER=batched`だけ変更して比較する。screen_swapを含む
他の設定は揃える。frame_interval、present、swap_top/bottom、make_current、
missing_s16と実際の音・映像を比較し、別区間へ待ちが移っただけなら改善とはしない。
メニューや手動スクリーンショットの操作は比較中に行わない。

スクリーンショットのあるフレームは両画面をSwap前に読み出すためbatchedへ戻る。
ログのrender_orderは選択した設定を表す。環境変数の未指定時はbatched。

### グリッドON時の統合比較

既定ではゲーム用グリッドを不透明ゲームシェーダへ融合し、各画面の別の全画面描画を省く。
既存の4×4画像・物理画面上の位置・GL_SRC_ALPHAのブレンド式を使い、
最終描画で1回だけ合成する。メニューは従来方式を維持する。
シェーダ／画像形式が対応しない場合は別パスへ戻る。

```sh
export DRASTIC_PROFILE=2
export DRASTIC_FUSED_GRID=1
export DRASTIC_PRESENT_ORDER=batched
unset DRASTIC_SWAP_INTERVAL
```

同じゲーム・同じステートから同じ場面を30～40秒測り、最初の5秒は除外する。
計測中はメニューや手動スクリーンショットを操作しない。
`AV display:`のgrid・fused_top/bottom・screen_swapも揃える。
次に`DRASTIC_FUSED_GRID=0`だけ変更して比較する。G＋L2でグリッド自体をOFFに
した結果も切り分けに使える。統合比較では`grid=1`を確認し、フラグが1でも
`fused_top/bottom=0`なら統合は動いていない。frame_interval、present、両方のswap、
missing_s16、実際の音と画面を比較し、待ち時間が別の処理へ移っただけでは改善としない。

Swapの待ちが大きい場合だけ、別の比較で`DRASTIC_SWAP_INTERVAL=0`を指定する。
各コンテキストに要求し、成功／失敗と実際の取得値を記録する。
設定してもKMSDRM／GPU側の待ちがなくなる保証はない。
`1`／`-1`も指定でき、未指定ならドライバの既定を維持する。
CPU周波数・音声設定・フレームスキップ・出力解像度は変更せず、
描画順序とswap intervalも同時に変更しない。

ゲーム画像の転送形式を比較する場合は、通常経路（BGRA）のログを取った後、
`DRASTIC_GAME_RGBA=1`を指定して同じ場面を再計測する。実験経路はゲーム画像を
RGBAとして転送し、表示シェーダで赤青を入れ替える。CPU画素変換は追加しない。
`Game upload mode`とLauncher行で選択値を確認し、frame_interval、upload、present、
missing_s16と実際の色・音を比較する。UI画像などゲーム画面以外のテクスチャ形式は変わらない。

通常利用に戻すときはSDカード直下のmain.shを`DRASTIC_PROFILE=0`にするか、
親シェルから0をexportする。比較用のswap intervalとPRESENT_ORDERはunsetする。

## 検証範囲

`python3 source/libhookdrastic/tests/test_changes.py`で、既存機能に加え
基本／詳細計測、元コールバックの命令照合、メニュー等の中断、音声ラッパー、
描画／Presentの分離、batched／groupedの順序・区間集計・撮影時の切り替え、
GLの状態・グリッドを合成するパス・解放、ログ保存の
衝突とフォールバックを確認する。SDL2_CONFIGとCCでホストのツールを指定できる。

GLのテストは模擬環境であり、実機のGPU性能や融合シェーダの実表示を検証するものではない。
