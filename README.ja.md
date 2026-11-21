[English](README.md) | 日本語

# DS RGDSPLUS JP+

[DEDICATED OS for RG DS Plus](https://github.com/dedicated-os/dedicated-rgds-plus) を日本語向けに調整した非公式パッケージです。オリジナル作者の作品を土台とし、その内容と方針を尊重しています。

追加機能は、日本語のゲーム名表示と、Hi-Resモードのオン／オフ切り替えです。

## 導入方法

RG DS Plusでは2枚のSDカードを使用します。TF1/INTにはオリジナルのシステムイメージを、TF2/EXTにはランチャーパッケージを入れます。

### 新規インストール

1. [オリジナルの `main-rgds-plus` Releases](https://github.com/dedicated-os/main-rgds-plus/releases) からシステムイメージをダウンロードし、[オリジナルプロジェクトの手順](https://github.com/dedicated-os/dedicated-rgds-plus)に従ってTF1/INT用SDカードに書き込みます。
2. オリジナルプロジェクトの説明に従ってTF2/EXT用SDカードを準備します。
3. 本リポジトリの[Releases](../../releases)から最新のJP+パッケージをダウンロードして解凍し、中身をTF2/EXTのルートにコピーします。
4. TF2/EXTの`/games/`にゲームを配置し、2枚のカードを本体に挿入して起動します。

### JP+のアップデート

1. [Releases](../../releases)から最新のJP+パッケージをダウンロードして解凍します。
2. `system.zip`、`bootlogo-0.bmp`、`bootlogo-1.bmp`をTF2/EXTのルートに上書きコピーします。
3. 本体を起動すると、起動時にシステムが更新されます。

## 操作方法

本体の **MENUボタン** を押すとゲーム内メニューが開きます。もう一度押すとシステムメニューが開きます。

| 操作 | ショートカット |
| :--- | :--- |
| Hi-Resモード切り替え | `MENU + START` |
| 上下画面の入れ替え | `MENU + SELECT` |
| 画面グリッドの切り替え | `MENU + L2` |
| スクリーンショット保存 | `MENU + A` |
| 明るさ調整 | `MENU + 音量 + / 音量 -` |
| 早送り | `BACK` |

![起動時の操作ガイド](github/bootlogo-1-preview.png)

Hi-Resモードを切り替えると、ゲームを自動で保存・再起動し、そのまま再開します。

## クレジット

RG DS Plus向けDEDICATED OSは[shauninman](https://github.com/dedicated-os/dedicated-rgds-plus)氏が制作・管理しています。ドキュメントとライセンスについては[オリジナルプロジェクト](https://github.com/dedicated-os/dedicated-rgds-plus)をご確認ください。
