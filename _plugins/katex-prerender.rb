# frozen_string_literal: true
#
# Renders math at build time with KaTeX, so math posts ship plain HTML and a
# stylesheet instead of a math engine (MathJax cost ~50MB per tab).
#
# Pages opt in with `math: true`. Delimiters and matching follow KaTeX's
# auto-render, which the site used in the browser before: $$...$$, \[...\],
# \(...\) and $...$, inside a single text node, outside pre/code/script/style.
# Kramdown turns $$...$$ into \[...\] or \(...\); single $ reaches the HTML as-is.
#
# KaTeX's CSS and fonts are copied from the gem into assets/katex/, so the
# stylesheet always matches the renderer. ExecJS runs KaTeX on Node.

require 'cgi'
require 'fileutils'
require 'json'
require 'katex'

module KatexPrerender
  DELIMITERS = [
    ['$$', '$$', true],
    ['\\[', '\\]', true],
    ['\\(', '\\)', false],
    ['$', '$', false]
  ].freeze
  LEFT = Regexp.union(DELIMITERS.map(&:first))
  SKIP_TAGS = %w[script noscript style textarea pre code option].freeze
  # Environments auto-render passes through with their delimiters attached.
  AMS = /\A\\begin\{/
  # Kramdown's typographic entities, which the browser decoded for auto-render.
  ENTITIES = {
    '&lsquo;' => "\u2018", '&rsquo;' => "\u2019", '&ldquo;' => "\u201C",
    '&rdquo;' => "\u201D", '&hellip;' => "\u2026", '&ndash;' => "\u2013",
    '&mdash;' => "\u2014", '&laquo;' => "\u00AB", '&raquo;' => "\u00BB",
    '&nbsp;' => "\u00A0"
  }.freeze

  class << self
    def render_page(doc)
      head, sep, body = doc.output.partition(/<body[^>]*>/)
      return if sep.empty?

      parts = split_body(body)
      math = parts.select { |part| part.is_a?(Array) }
      return if math.empty?

      html = renderer.call('renderAll', math)
      doc.output = head + sep + parts.map { |part| part.is_a?(Array) ? html.shift : part }.join
    end

    def copy_assets(site)
      dest = File.join(site.dest, 'assets', 'katex')
      vendor = File.join(Katex.gem_path, 'vendor', 'katex')
      FileUtils.mkdir_p(File.join(dest, 'fonts'))
      FileUtils.cp(File.join(vendor, 'stylesheets', 'katex.css'), dest)
      FileUtils.cp(Dir[File.join(vendor, 'fonts', '*.woff2')], File.join(dest, 'fonts'))
    end

    private

    # Splits HTML into strings (kept verbatim) and [tex, display] pairs.
    def split_body(body)
      skip = 0
      body.split(/(<[^>]*>)/).flat_map do |chunk|
        if chunk.start_with?('<')
          name = chunk[%r{\A</?([a-zA-Z]+)}, 1]&.downcase
          skip += chunk.start_with?('</') ? -1 : 1 if SKIP_TAGS.include?(name) && !chunk.end_with?('/>')
          [chunk]
        elsif skip.positive?
          [chunk]
        else
          split_text(chunk)
        end
      end
    end

    # auto-render's splitAtDelimiters: leftmost opening delimiter wins;
    # unmatched delimiters stay text.
    def split_text(text)
      out = []
      while (start = text.index(LEFT))
        left, right, display = DELIMITERS.find { |l, _, _| text[start..].start_with?(l) }
        stop = find_end(right, text, start + left.length)
        break unless stop

        out << text[0...start] unless start.zero?
        raw = text[start...(stop + right.length)]
        tex = raw.match?(AMS) ? raw : text[(start + left.length)...stop]
        out << [decode(tex), display]
        text = text[(stop + right.length)..]
      end
      out << text unless text.empty?
      out
    end

    # auto-render's findEndOfMath: ignores escaped characters and delimiters
    # inside braces.
    def find_end(delim, text, index)
      depth = 0
      while index < text.length
        return index if depth <= 0 && text[index, delim.length] == delim

        case text[index]
        when '\\' then index += 1
        when '{' then depth += 1
        when '}' then depth -= 1
        end
        index += 1
      end
      nil
    end

    def decode(tex)
      CGI.unescapeHTML(tex.gsub(/&[a-z]+;/) { |e| ENTITIES.fetch(e, e) })
    end

    # One Node process per page rather than per formula.
    def renderer
      @renderer ||= ExecJS.compile(File.read(Katex.katex_js_path) + <<~JS)
        function renderAll(items) {
          return items.map(function (item) {
            return katex.renderToString(item[0], { displayMode: item[1], throwOnError: false });
          });
        }
      JS
    end
  end
end

Jekyll::Hooks.register [:posts, :pages], :post_render do |doc|
  KatexPrerender.render_page(doc) if doc.data['math']
end

Jekyll::Hooks.register :site, :post_write do |site|
  KatexPrerender.copy_assets(site)
end
