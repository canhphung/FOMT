/* Small local test adapter, compiled against the user's mGBA checkout.
 * Does not contain game data, firmware, or mGBA source. */
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/log.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/arm/isa-inlines.h>
#include <stdlib.h>
#include <string.h>

static unsigned error_count;
static void probe_log(struct mLogger* l, int cat, enum mLogLevel level, const char* fmt, va_list args) {
    (void)l; (void)cat;
    if (level & (mLOG_FATAL | mLOG_ERROR)) {
        ++error_count;
        vfprintf(stderr, fmt, args);
        fputc('\n', stderr);
    }
}
static struct mLogger logger = { .log = probe_log, .filter = NULL };
unsigned session_errors(void) { return error_count; }

struct Session { struct mCore* core; uint32_t pixels[240*160]; };

void* session_open(const char* path) {
    mLogSetDefaultLogger(&logger);
    struct Session* s = calloc(1, sizeof(*s));
    if (!s) return NULL;
    s->core = mCoreFind(path);
    if (!s->core || !s->core->init(s->core)) { free(s); return NULL; }
    mCoreInitConfig(s->core, NULL);
    mCoreConfigSetDefaultIntValue(&s->core->config, "useBios", 0);
    mCoreConfigSetDefaultIntValue(&s->core->config, "skipBios", 1);
    mCoreLoadConfig(s->core);
    s->core->setVideoBuffer(s->core, s->pixels, 240);
    if (!mCoreLoadFile(s->core, path)) { s->core->deinit(s->core); free(s); return NULL; }
    s->core->reset(s->core);
    return s;
}
void session_close(struct Session* s) {
    if (!s) return;
    mCoreConfigDeinit(&s->core->config);
    s->core->deinit(s->core);
    free(s);
}
void session_frames(struct Session* s, unsigned frames, unsigned keys) {
    s->core->setKeys(s->core, keys);
    while (frames--) s->core->runFrame(s->core);
}
uint32_t* session_pixels(struct Session* s) { return s->pixels; }
uint32_t session_read(struct Session* s, uint32_t address) { return s->core->busRead8(s->core, address); }
void session_write(struct Session* s, uint32_t address, unsigned value) { s->core->busWrite8(s->core, address, value); }
uint32_t session_reg(struct Session* s, unsigned index) { return ((struct ARMCore*)s->core->cpu)->gprs[index]; }
size_t session_state_size(struct Session* s) { return s->core->stateSize(s->core); }
int session_save(struct Session* s, void* data) { return s->core->saveState(s->core, data); }
int session_load(struct Session* s, void* data) { return s->core->loadState(s->core, data); }
size_t session_export_sram(struct Session* s, void* out, size_t capacity) {
    void* data = NULL;
    size_t size = s->core->savedataClone(s->core, &data);
    if (size && data && size <= capacity) memcpy(out, data, size);
    free(data);
    return size;
}
int session_import_sram(struct Session* s, const void* data, size_t size) {
    /* No auto-loaded save file is attached by this adapter. Copy into the
     * SRAM backing store; a transient mask is unsuitable for power-cycle tests. */
    return s->core->savedataRestore(s->core, data, size, true);
}
void session_reset(struct Session* s) { s->core->reset(s->core); }
/* Isolated function probe. Save/restore emulator state around use from Python.
 * Real ARM7TDMI execution using the game's initialized IWRAM routines. */
int session_call(struct Session* s, uint32_t address, uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3) {
    struct ARMCore* cpu = s->core->cpu;
    cpu->gprs[0] = r0; cpu->gprs[1] = r1; cpu->gprs[2] = r2; cpu->gprs[3] = r3;
    cpu->gprs[13] = 0x03007000;
    cpu->gprs[14] = 0x0203F001;
    s->core->busWrite16(s->core, 0x0203F000, 0xE7FE);
    _ARMSetMode(cpu, MODE_THUMB);
    cpu->gprs[15] = address & ~1u;
    ThumbWritePC(cpu);
    for (unsigned i = 0; i < 100000; ++i) {
        if ((uint32_t)cpu->gprs[15] == 0x0203F002) return 1;
        s->core->step(s->core);
    }
    return 0;
}
