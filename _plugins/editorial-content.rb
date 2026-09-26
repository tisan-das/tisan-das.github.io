# frozen_string_literal: true
#
# Post-processes posts (_layouts/post.html), standing in for what Chirpy's
# own post layout did through refactor-content.html:
#
# - Images: lazy loading, and real width/height so text doesn't jump as they
#   load (and table-of-contents links land in the right place). Chirpy's
#   `{: w="1200" h="500"}` become width/height; other images are sized from
#   the file. An image that sets `loading` itself, like the hero, is left
#   to load eagerly.
# - Code blocks: a header with the language (or `{: file='...'}` name) and a
#   copy button, built here so nothing shifts in when scripts run. Fences in
#   a language Rouge doesn't know (```curl) arrive as a bare <pre>; they get
#   the same frame, unhighlighted.
# - Tables: wrapped so a wide one scrolls sideways instead of the page.
# - Figures: paragraphs holding only images (and an _italic_ caption) get
#   class="figure". Text written directly above an image, with no blank line,
#   shares its paragraph; that text is split off into a paragraph of its own.

require 'cgi'
require 'uri'

module EditorialContent
  # Rouge language names as readers know them; anything else is capitalized.
  LANGUAGES = {
    'bash' => 'Shell', 'sh' => 'Shell', 'zsh' => 'Shell', 'shell' => 'Shell',
    'c' => 'C', 'cpp' => 'C++', 'cs' => 'C#', 'csharp' => 'C#', 'go' => 'Go',
    'java' => 'Java', 'js' => 'JavaScript', 'javascript' => 'JavaScript',
    'ts' => 'TypeScript', 'typescript' => 'TypeScript',
    'py' => 'Python', 'python' => 'Python', 'python3' => 'Python',
    'rb' => 'Ruby', 'rs' => 'Rust', 'yml' => 'YAML', 'yaml' => 'YAML',
    'json' => 'JSON', 'xml' => 'XML', 'html' => 'HTML', 'css' => 'CSS',
    'sql' => 'SQL', 'http' => 'HTTP', 'toml' => 'TOML', 'dockerfile' => 'Dockerfile',
    'conf' => 'Config', 'curl' => 'curl', 'text' => 'Text', 'plaintext' => 'Text'
  }.freeze

  # What a figure paragraph may hold besides nothing: images, line breaks, a caption.
  FIGURE_BITS = %r{<img\b[^>]*>|<br\s*/?>|<em>.*?</em>|\s}m

  COPY_ICON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' \
              'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' \
              '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>'

  class << self
    def process(post)
      head, sep, rest = post.output.partition(/<article class="post"[^>]*>/)
      return if sep.empty?

      body, close, tail = rest.partition('</article>')

      body = body.gsub(/<img\b[^>]*>/) { |tag| image(tag, post.site.source) }
      body = body.gsub(%r{<p>(.*?)</p>}m) { paragraph(Regexp.last_match(1)) }
      body = body.gsub(%r{<pre><code class="language-([\w+#-]+)">(.*?)</code></pre>}m) do
        %(<div class="language-#{$1} highlighter-rouge"><div class="highlight"><pre class="highlight"><code>#{$2}</code></pre></div></div>)
      end
      # Rouge's line-number tables sit inside code blocks, which scroll already.
      body = body.gsub(%r{<table\b(?![^>]*rouge-table).*?</table>}m) { |table| %(<div class="table-wrapper">#{table}</div>) }
      body = body.gsub(/<div\b[^>]*\bclass="language-([\w+#-]+) highlighter-rouge"[^>]*>/) do |div|
        lang = Regexp.last_match(1)
        div + code_header(div[/\sfile="([^"]*)"/, 1] || label(lang))
      end
      post.output = head + sep + body + close + tail
    end

    private

    def image(tag, source)
      tag = tag.gsub(/\s(w|h)=(["'])/) { " #{$1 == 'w' ? 'width' : 'height'}=#{$2}" }
      width = tag[/\swidth=["']?(\d+)/, 1]
      height = tag[/\sheight=["']?(\d+)/, 1]
      unless width && height
        size = size_of(tag[/\ssrc="([^"]+)"/, 1], source)
        if size
          # Keep a size the author gave; fill in the other from the file's ratio.
          if width then height = width.to_i * size[1] / size[0]
          elsif height then width = height.to_i * size[0] / size[1]
          else width, height = size
          end
          tag = tag.gsub(/\s(?:width|height)=["']?\w+["']?/, '')
                   .sub(/<img\b/) { %(<img width="#{width}" height="#{height}") }
        end
      end
      tag = tag.sub(/<img\b/, '<img loading="lazy" decoding="async"') unless tag.include?('loading=')
      tag
    end

    def paragraph(inner)
      return "<p>#{inner}</p>" unless inner.include?('<img')
      return %(<p class="figure">#{inner}</p>) if inner.gsub(FIGURE_BITS, '').empty?

      text, figure = inner.split(/(?=<img\b)/, 2)
      return "<p>#{inner}</p>" unless figure&.gsub(FIGURE_BITS, '')&.empty?

      %(<p>#{text.sub(%r{(?:\s|<br\s*/?>)+\z}, '')}</p>\n<p class="figure">#{figure}</p>)
    end

    def size_of(src, source)
      return unless src&.start_with?('/') && !src.start_with?('//')

      ImageDimensions.read(File.join(source, URI.decode_uri_component(src.split(/[?#]/).first)))
    end

    def label(lang)
      LANGUAGES.fetch(lang.downcase) { lang.capitalize }
    end

    def code_header(text)
      %(<div class="code-header"><span>#{CGI.escapeHTML(CGI.unescapeHTML(text))}</span>) +
        %(<button type="button" aria-label="Copy code">#{COPY_ICON}</button></div>)
    end
  end
end

Jekyll::Hooks.register :posts, :post_render do |post|
  EditorialContent.process(post) if post.data['layout'] == 'post'
end
