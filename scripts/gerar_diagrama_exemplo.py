"""Gera um diagrama de arquitetura de exemplo (PNG) para demonstrar a API."""

from pathlib import Path

from PIL import Image, ImageDraw

SAIDA = Path(__file__).resolve().parent.parent / "images" / "exemplo_diagrama.png"


def caixa(d, xy, texto, cor):
    d.rounded_rectangle(xy, radius=12, fill=cor, outline="black", width=2)
    x0, y0, x1, y1 = xy
    d.text(((x0 + x1) / 2 - len(texto) * 3, (y0 + y1) / 2 - 6), texto, fill="black")


def seta(d, a, b):
    d.line([a, b], fill="black", width=3)
    d.polygon([(b[0], b[1]), (b[0] - 12, b[1] - 7), (b[0] - 12, b[1] + 7)], fill="black")


def main():
    img = Image.new("RGB", (900, 420), "white")
    d = ImageDraw.Draw(img)
    d.rectangle((300, 40, 880, 390), outline="red", width=2)
    d.text((310, 46), "Fronteira de confianca (rede interna)", fill="red")
    caixa(d, (30, 160, 190, 240), "Usuario / Browser", "#cfe8ff")
    caixa(d, (330, 160, 520, 240), "API Gateway / Backend", "#d9f2d9")
    caixa(d, (690, 160, 860, 240), "Banco de Dados", "#ffe9b3")
    caixa(d, (330, 300, 520, 360), "Servico de Autenticacao", "#f3d1f3")
    seta(d, (190, 200), (330, 200))
    seta(d, (520, 200), (690, 200))
    seta(d, (425, 240), (425, 300))
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    img.save(SAIDA)
    print(f"Diagrama salvo em {SAIDA}")


if __name__ == "__main__":
    main()
