#let manuscript(
  title: "Manuscript Title",
  running-head: none,
  authors: (),
  affiliations: (),
  corresponding: none,
  abstract: none,
  body
) = {
  // Page setup conforming to double-spaced clinical paper standards
  set page(
    paper: "us-letter",
    margin: (x: 1in, y: 1in),
    header: locate(loc => {
      let page_number = counter(page).at(loc).first()
      if page_number > 1 and running-head != none [
        #text(size: 8.5pt, fill: rgb("555555"))[
          #running-head
          #h(1fr)
          #page_number
        ]
      ]
    }),
    footer: locate(loc => {
      let page_number = counter(page).at(loc).first()
      if page_number == 1 [
        #align(center, text(size: 10pt)[#page_number])
      ]
    })
  )

  // Double line spacing (1.5em leading in typst is equivalent to double space)
  set text(font: "Georgia", size: 11pt)
  set par(leading: 1.25em, justify: true, first-line-indent: 0.5in)
  show par: set block(spacing: 1.25em)

  // Title Page Layout
  if title != none {
    align(center)[
      #v(2.5cm)
      #text(size: 18pt, weight: "bold")[#title]
      #v(1.5cm)
      #text(size: 11pt)[
        #authors.join(", ")
      ]
      #v(1cm)
      #text(size: 9.5pt, fill: rgb("444444"))[
        #affiliations.join("\n")
      ]
      #v(2.5cm)
      #if corresponding != none [
        #align(left)[
          #text(size: 9pt, style: "italic")[
            *Corresponding Author:* \
            #corresponding
          ]
        ]
      ]
    ]
    pagebreak()
  }

  // Abstract Layout (always on a separate page)
  if abstract != none {
    align(center)[
      #text(size: 14pt, weight: "bold")[Abstract]
    ]
    #v(0.5cm)
    #set par(first-line-indent: 0in)
    #abstract
    #pagebreak()
  }

  // Enable continuous line numbering for peer review in the main body
  set par.line(numbering: "1")

  // Heading styles
  show heading: it => block(below: 1em, above: 1.5em)[
    #set text(font: "Arial", weight: "bold", fill: black)
    #if it.level == 1 {
      align(center, text(size: 14pt)[#it.body])
    } else if it.level == 2 {
      text(size: 12pt)[#it.body]
    } else {
      text(size: 11pt, style: "italic")[#it.body]
    }
  ]

  // Scientific Three-line Table configurations
  show table: set block(breakable: false)
  set table(
    stroke: (x, y) => if y == 0 {
      (top: 1.5pt + black, bottom: 0.75pt + black)
    } else {
      none
    }
  )

  // `body` is already resolved by Pandoc citeproc, including in-text
  // citations and References. Do not call `bibliography()` here: doing so
  // would introduce a second citation engine and backend-dependent output.
  body
}
