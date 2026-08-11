export default function Home() {
  const title = 'JioSaavn API'
  const description =
    'JioSaavn API is an unofficial wrapper written in TypeScript for jiosaavn.com providing programmatic access to a vast library of songs, albums, artists, playlists, and more.'

  const Meteors = ({ number }: { number: number }) => {
    return (
      <>
        {Array.from({ length: number || 20 }, (_, idx) => (
          <span
            key={idx}
            className="meteor animate-[meteorAnimation_3s_linear_infinite] absolute h-1 w-1 rounded-[9999px] shadow-[0_0_0_1px_#ffffff10] rotate-[215deg]"
            style={{
              top: 0,
              left: `${Math.floor(Math.random() * (400 - -400) + -400)}px`,
              animationDelay: `${Math.random() * (0.8 - 0.2) + 0.2}s`,
              animationDuration: `${Math.floor(Math.random() * (10 - 2) + 2)}s`
            }}
          />
        ))}
      </>
    )
  }

  return (
    <div className="bg-black min-h-screen">
      <title>{title}</title>
      <main className="mx-auto my-auto flex flex-col space-y-8 px-4 pb-8 md:py-10 relative overflow-y-hidden overflow-x-hidden max-w-screen-lg">
        <Meteors number={15} />

        <div className="flex flex-row items-center space-x-4 ml-6">
          <svg className="sm:h-12 sm:w-12 h-8 w-8 shrink-0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path
              fill="#ff7d78"
              d="M3.172 3.464C2 4.93 2 7.286 2 12c0 4.714 0 7.071 1.172 8.535C4.343 22 6.229 22 10 22h3.376A4.25 4.25 0 0 1 17 16.007V12.25a2.25 2.25 0 0 1 4.5 0a.75.75 0 0 0 .5.707V12c0-4.714 0-7.071-1.172-8.536C19.657 2 17.771 2 14 2h-4C6.229 2 4.343 2 3.172 3.464"
              opacity=".5"
            />
            <path
              fill="#ff7d78"
              fillRule="evenodd"
              d="M8.25 12a3.75 3.75 0 1 1 7.5 0a3.75 3.75 0 0 1-7.5 0m11-.5a.75.75 0 0 1 .75.75a2.25 2.25 0 0 0 2.25 2.25a.75.75 0 0 1 0 1.5a3.734 3.734 0 0 1-2.25-.75v5a2.75 2.75 0 1 1-1.5-2.45v-5.55a.75.75 0 0 1 .75-.75m-.75 8.75a1.25 1.25 0 1 0-2.5 0a1.25 1.25 0 0 0 2.5 0"
              clipRule="evenodd"
            />
          </svg>
          <p className="text-2xl md:text-4xl text-transparent font-bold leading-none bg-clip-text bg-gradient-to-r from-[#ff7d78] to-purple-600">
            JioSaavn API
            <span className="uppercase text-sm ml-3 text-gray-500 font-normal sm:hidden">Unofficial</span>
          </p>
          <p className="hidden sm:block animate-[borderAnimation_3s_linear_infinite] rounded bg-gradient-to-r from-red-500 via-purple-500 to-blue-500 bg-[length:400%_400%] p-1">
            <span className="block rounded px-1.5 py-0.5 text-xs text-white uppercase tracking-wider">Unofficial</span>
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 lg:grid-cols-4 xl:grid-cols-8 gap-2 sm:gap-0 relative grid-flow-row">
          <a
            target="_blank"
            rel="noopener noreferrer"
            className="p-4 sm:p-8 hover:bg-opacity-5 hover:bg-white rounded-lg duration-100 sm:col-span-4"
            href="/api/docs"
          >
            <div className="flex flex-col">
              <span className="text-xs uppercase bg-opacity-15 rounded text-center max-w-fit px-2 py-1 font-bold tracking-wide bg-red-500 text-red-500">
                Get Started
              </span>
              <span className="text-neutral-200 font-bold text-lg sm:text-xl md:text-2xl mt-2">Explore the Docs</span>
              <div className="text-neutral-500 mt-2">
                Check out the documentation to learn how to use the JioSaavn API.
              </div>
            </div>
          </a>

          <a
            target="_blank"
            rel="noopener noreferrer"
            className="p-4 sm:p-8 hover:bg-opacity-5 hover:bg-white rounded-lg duration-100 sm:col-span-4"
            href="https://github.com/sumitkolhe/jiosaavn-api"
          >
            <div className="flex flex-col">
              <span className="text-xs uppercase bg-opacity-15 rounded text-center max-w-fit px-2 py-1 font-bold tracking-wide bg-green-500 text-green-500">
                Open Source
              </span>
              <span className="text-neutral-200 font-bold text-lg sm:text-xl md:text-2xl mt-2">Open Source</span>
              <div className="text-neutral-500 mt-2">Saavn API is open-source. Check out the source code on github.</div>
            </div>
          </a>

          <a
            target="_blank"
            rel="noopener noreferrer"
            className="p-4 sm:p-8 hover:bg-opacity-5 hover:bg-white rounded-lg duration-100 sm:col-span-4"
            href="https://github.com/sumitkolhe/jiosaavn-api/issues"
          >
            <div className="flex flex-col">
              <span className="text-xs uppercase bg-opacity-15 rounded text-center max-w-fit px-2 py-1 font-bold tracking-wide bg-violet-500 text-violet-500">
                Contribute
              </span>
              <span className="text-neutral-200 font-bold text-lg sm:text-xl md:text-2xl mt-2">Get Involved</span>
              <div className="text-neutral-500 mt-2">
                Encounter a bug or have a feature suggestion? Report it on GitHub or contribute by submitting a pull request.
              </div>
            </div>
          </a>

          <div className="p-4 sm:p-8 hover:bg-opacity-5 hover:bg-white rounded-lg duration-100 sm:col-span-4">
            <div className="flex flex-col">
              <span className="text-xs uppercase bg-opacity-15 rounded text-center max-w-fit px-2 py-1 font-bold tracking-wide bg-blue-500 text-blue-500">
                Contact
              </span>
              <span className="text-neutral-200 font-bold text-lg sm:text-xl md:text-2xl mt-2">Sumit Kolhe</span>
              <div className="text-neutral-500 mt-2">
                Have a question or need help? Reach out on{' '}
                <a
                  href="https://github.com/sumitkolhe"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline text-indigo-500"
                >
                  GitHub
                </a>
                ,{' '}
                <a
                  href="https://twitter.com/thesumitkolhe"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline text-sky-500"
                >
                  Twitter
                </a>
                , or{' '}
                <a
                  href="https://t.me/sumitkolhe"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline text-pink-500"
                >
                  Telegram.
                </a>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
