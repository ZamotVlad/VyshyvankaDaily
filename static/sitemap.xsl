<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:sitemap="http://www.sitemaps.org/schemas/sitemap/0.9">
<xsl:output method="html" encoding="UTF-8" indent="yes"/>
<xsl:template match="/">
<html lang="uk">
<head>
  <meta charset="utf-8"/>
  <title>Sitemap - VyshyvankaDaily</title>
  <style>
    body { font-family: -apple-system, sans-serif; background: #111; color: #eee; padding: 2rem; }
    h1 { color: #e46b6b; }
    .count { color: #999; margin-bottom: 1.5rem; }
    table { width: 100%; border-collapse: collapse; }
    th { text-align: left; padding: 0.6rem; border-bottom: 2px solid #e46b6b; color: #e46b6b; }
    td { padding: 0.5rem 0.6rem; border-bottom: 1px solid #333; font-size: 0.9rem; }
    tr:hover { background: #1c1c1c; }
    a { color: #7fbfff; text-decoration: none; word-break: break-all; }
    a:hover { text-decoration: underline; }
    .meta { color: #888; white-space: nowrap; }
  </style>
</head>
<body>
  <h1>VyshyvankaDaily - Sitemap</h1>
  <p class="count">
    Усього URL: <xsl:value-of select="count(sitemap:urlset/sitemap:url)"/>
  </p>
  <table>
    <tr>
      <th>URL</th>
      <th>Оновлено</th>
      <th>Частота</th>
      <th>Пріоритет</th>
    </tr>
    <xsl:for-each select="sitemap:urlset/sitemap:url">
    <tr>
      <td><a href="{sitemap:loc}"><xsl:value-of select="sitemap:loc"/></a></td>
      <td class="meta"><xsl:value-of select="sitemap:lastmod"/></td>
      <td class="meta"><xsl:value-of select="sitemap:changefreq"/></td>
      <td class="meta"><xsl:value-of select="sitemap:priority"/></td>
    </tr>
    </xsl:for-each>
  </table>
</body>
</html>
</xsl:template>
</xsl:stylesheet>