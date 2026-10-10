# Menghubungkan code assistant lain

Setiap code assistant yang mendukung MCP bisa membaca Zul lewat perintah yang sama, `zul mcp serve`. Yang berbeda hanya letak dan bentuk file config-nya. Panduan ini berisi config untuk Claude Code, Cursor, VS Code, dan Claude Desktop, serta cara memakai Zul langsung dari checkout repository.

**Sebelum mulai:** Zul sudah ter-install dengan extra `mcp`, dan `zul mcp check` mencetak `MCP server zul siap`. Langkahnya ada di dua bagian pertama [tutorial code assistant](../tutorial/code-assistant.md).

## Mencetak config

`zul mcp config` mencetak config yang siap ditempel untuk satu client. Pilihan client-nya `claude-code`, `cursor`, `vscode`, dan `claude-desktop`:

```shell
zul mcp config cursor
```

Keluarannya untuk Cursor dan Claude Desktop sama:

```json
{
  "mcpServers": {
    "zul": {
      "command": "zul",
      "args": [
        "mcp",
        "serve"
      ]
    }
  }
}
```

Jika file config client sudah berisi server lain, salin hanya entri `"zul"` ke dalam `"mcpServers"` yang sudah ada.

## Claude Code

Untuk semua proyek, daftarkan server dengan satu perintah:

```shell
claude mcp add --scope user zul -- zul mcp serve
```

Untuk satu proyek yang dipakai bersama tim, simpan config di file `.mcp.json` di root proyek, lalu commit file itu. Isinya sama dengan keluaran `zul mcp config claude-code` di atas. Saat proyek dibuka, Claude Code menanyakan apakah server dari file itu boleh dijalankan.

Periksa hasilnya dengan `claude mcp list`, atau dengan `/mcp` di dalam sesi Claude Code.

## Cursor

1. Cetak config-nya:

    ```shell
    zul mcp config cursor
    ```

2. Tempel keluarannya ke `~/.cursor/mcp.json` untuk semua proyek, atau ke `.cursor/mcp.json` di root proyek untuk satu proyek saja.

3. Buka pengaturan MCP di Cursor. Server `zul` tampil beserta sembilan tool-nya.

## VS Code

MCP server di VS Code dipakai oleh GitHub Copilot Chat dalam mode Agent. Bentuk config-nya berbeda dari client lain: kuncinya `"servers"`, dan setiap server menyebut jenis transport-nya.

1. Cetak config-nya:

    ```shell
    zul mcp config vscode
    ```

    Keluarannya:

    ```json
    {
      "servers": {
        "zul": {
          "type": "stdio",
          "command": "zul",
          "args": [
            "mcp",
            "serve"
          ]
        }
      }
    }
    ```

2. Simpan keluaran itu sebagai `.vscode/mcp.json` di root proyek. Untuk semua proyek, jalankan perintah **MCP: Open User Configuration** dari Command Palette, lalu tempel entri `"zul"` di sana.

3. Jalankan perintah **MCP: List Servers**. Server `zul` tampil dan bisa dinyalakan dari daftar itu.

## Claude Desktop

1. Cetak config-nya:

    ```shell
    zul mcp config claude-desktop
    ```

2. Di Claude Desktop, buka **Settings**, pilih **Developer**, lalu klik **Edit Config**. File yang terbuka adalah `claude_desktop_config.json`: di Windows letaknya `%APPDATA%\Claude\claude_desktop_config.json`, dan di macOS `~/Library/Application Support/Claude/claude_desktop_config.json`.

3. Tempel keluaran langkah 1, simpan, lalu tutup Claude Desktop sepenuhnya dan buka lagi. Config hanya dibaca saat aplikasi dibuka.

## Memakai Zul dari checkout repository

Saat kamu sedang mengubah Zul, code assistant sebaiknya membaca kode di checkout-mu, bukan versi yang ter-install. Tambahkan `--repo` dengan path checkout itu:

```shell
zul mcp config cursor --repo ~/projek/zul_utilities
```

Config yang tercetak menjalankan server lewat uv di folder itu, sehingga setiap perubahan kode dan dokumentasi langsung terbaca di sesi berikutnya:

```json
{
  "mcpServers": {
    "zul": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/kamu/projek/zul_utilities",
        "run",
        "--no-dev",
        "--extra",
        "mcp",
        "zul",
        "mcp",
        "serve"
      ]
    }
  }
}
```

`--no-dev` membuat uv hanya meng-install Zul dan extra `mcp` di checkout yang belum pernah di-install, tanpa PyTorch dan library dev lainnya. Library yang sudah ada di environment tidak dihapus.

Repository Zul sudah berisi `.mcp.json` dengan perintah yang sama. Jadi Claude Code yang dibuka di checkout Zul langsung menawarkan server `zul` tanpa config tambahan.

## Jika server tidak tersambung

Tabel berikut mencantumkan masalah yang paling sering muncul beserta penyelesaiannya:

| Gejala | Penyebab | Penyelesaian |
|---|---|---|
| Client melaporkan perintah `zul` tidak ditemukan | Aplikasi yang dibuka dari menu, seperti Claude Desktop, tidak selalu membaca `PATH` dari terminal. | Ganti `"zul"` di `"command"` dengan path lengkap dari `which zul`, atau `where zul` di Windows. Di JSON, tulis backslash path Windows dua kali, misalnya `C:\\Users\\kamu\\.local\\bin\\zul.exe`. |
| Log server berisi `MCP server butuh extra mcp` | `zul` yang dijalankan client berasal dari instalasi tanpa extra `mcp`. | Install ulang dengan extra `mcp`, atau arahkan `"command"` ke `zul` yang punya extra itu. |
| Server tersambung, tetapi tool baru tidak muncul | Daftar tool dibaca saat server dinyalakan. | Mulai ulang sesi code assistant, atau nyalakan ulang server dari daftar MCP di client. |

## Halaman terkait

- [Tutorial: Menghubungkan Zul ke code assistant](../tutorial/code-assistant.md)
- [Referensi: MCP server](../referensi/mcp.md)
- [Referensi: Perintah zul](../referensi/cli.md)
