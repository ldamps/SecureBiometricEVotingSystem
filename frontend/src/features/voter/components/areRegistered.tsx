// Component to check if the voter is registered to vote

function AreRegistered({next, state, setState}: {next: () => void, state: any, setState: (state: any) => void}) {
    return (
        <div>
            <h1>Are you registered to vote?</h1>
        </div>
    )
}

export default AreRegistered;